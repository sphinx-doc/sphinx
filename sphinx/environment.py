# -*- coding: utf-8 -*-
"""
    sphinx.environment
    ~~~~~~~~~~~~~~~~~~

    Global creation environment.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import re
import os
import time
import heapq
import difflib
import itertools
import cPickle as pickle
from os import path
from string import uppercase
try:
    import hashlib
    md5 = hashlib.md5
except:
    # 2.4 compatibility
    import md5
    md5 = md5.new

from docutils import nodes
from docutils.io import FileInput
from docutils.core import publish_doctree
from docutils.utils import Reporter
from docutils.readers import standalone
from docutils.transforms import Transform
from docutils.transforms.parts import ContentsFilter
from docutils.transforms.universal import FilterMessages

# monkey-patch reST parser to disable alphabetic and roman enumerated lists
from docutils.parsers.rst.states import Body
Body.enum.converters['loweralpha'] = \
    Body.enum.converters['upperalpha'] = \
    Body.enum.converters['lowerroman'] = \
    Body.enum.converters['upperroman'] = lambda x: None

from sphinx import addnodes
from sphinx.util import get_matching_docs, SEP
from sphinx.directives import additional_xref_types

default_settings = {
    'embed_stylesheet': False,
    'cloak_email_addresses': True,
    'pep_base_url': 'http://www.python.org/dev/peps/',
    'input_encoding': 'utf-8',
    'doctitle_xform': False,
    'sectsubtitle_xform': False,
}

# This is increased every time a new environment attribute is added
# to properly invalidate pickle files.
ENV_VERSION = 17


def walk_depth(node, depth, maxdepth):
    """Utility: Cut a TOC at a specified depth."""
    for subnode in node.children[:]:
        if isinstance(subnode, (addnodes.compact_paragraph, nodes.list_item)):
            walk_depth(subnode, depth, maxdepth)
        elif isinstance(subnode, nodes.bullet_list):
            if depth > maxdepth:
                subnode.parent.replace(subnode, [])
            else:
                walk_depth(subnode, depth+1, maxdepth)


default_substitutions = set([
    'version',
    'release',
    'today',
])


class RedirStream(object):
    def __init__(self, writefunc):
        self.writefunc = writefunc
    def write(self, text):
        if text.strip():
            self.writefunc(text)


class NoUri(Exception):
    """Raised by get_relative_uri if there is no URI available."""
    pass


class DefaultSubstitutions(Transform):
    """
    Replace some substitutions if they aren't defined in the document.
    """
    # run before the default Substitutions
    default_priority = 210

    def apply(self):
        config = self.document.settings.env.config
        # only handle those not otherwise defined in the document
        to_handle = default_substitutions - set(self.document.substitution_defs)
        for ref in self.document.traverse(nodes.substitution_reference):
            refname = ref['refname']
            if refname in to_handle:
                text = config[refname]
                if refname == 'today' and not text:
                    # special handling: can also specify a strftime format
                    text = time.strftime(config.today_fmt)
                ref.replace_self(nodes.Text(text, text))


class MoveModuleTargets(Transform):
    """
    Move module targets to their nearest enclosing section title.
    """
    default_priority = 210

    def apply(self):
        for node in self.document.traverse(nodes.target):
            if not node['ids']:
                continue
            if node['ids'][0].startswith('module-') and \
                   node.parent.__class__ is nodes.section:
                node.parent['ids'] = node['ids']
                node.parent.remove(node)


class MyStandaloneReader(standalone.Reader):
    """
    Add our own transforms.
    """
    def get_transforms(self):
        tf = standalone.Reader.get_transforms(self)
        return tf + [DefaultSubstitutions, MoveModuleTargets,
                     FilterMessages]


class MyContentsFilter(ContentsFilter):
    """
    Used with BuildEnvironment.add_toc_from() to discard cross-file links
    within table-of-contents link nodes.
    """
    def visit_pending_xref(self, node):
        self.parent.append(nodes.literal(node['reftarget'], node['reftarget']))
        raise nodes.SkipNode


class BuildEnvironment:
    """
    The environment in which the ReST files are translated.
    Stores an inventory of cross-file targets and provides doctree
    transformations to resolve links to them.

    Not all doctrees are stored in the environment, only those of files
    containing a "toctree" directive, because they have to change if sections
    are edited in other files. This keeps the environment size moderate.
    """

    # --------- ENVIRONMENT PERSISTENCE ----------------------------------------

    @staticmethod
    def frompickle(filename):
        picklefile = open(filename, 'rb')
        try:
            env = pickle.load(picklefile)
        finally:
            picklefile.close()
        if env.version != ENV_VERSION:
            raise IOError('env version not current')
        return env

    def topickle(self, filename):
        # remove unpicklable attributes
        warnfunc = self._warnfunc
        self.set_warnfunc(None)
        picklefile = open(filename, 'wb')
        try:
            pickle.dump(self, picklefile, pickle.HIGHEST_PROTOCOL)
        finally:
            picklefile.close()
        # reset stream
        self.set_warnfunc(warnfunc)

    # --------- ENVIRONMENT INITIALIZATION -------------------------------------

    def __init__(self, srcdir, doctreedir, config):
        self.doctreedir = doctreedir
        self.srcdir = srcdir
        self.config = config

        # the docutils settings for building
        self.settings = default_settings.copy()
        self.settings['env'] = self

        # the function to write warning messages with
        self._warnfunc = None

        # this is to invalidate old pickles
        self.version = ENV_VERSION

        # All "docnames" here are /-separated and relative and exclude the source suffix.

        self.found_docs = set()     # contains all existing docnames
        self.all_docs = {}          # docname -> (mtime, md5sum) at the time of build
                                    # contains all built docnames

        # File metadata
        self.metadata = {}          # docname -> dict of metadata items

        # TOC inventory
        self.titles = {}            # docname -> title node
        self.tocs = {}              # docname -> table of contents nodetree
        self.toc_num_entries = {}   # docname -> number of real entries
                                    # used to determine when to show the TOC in a sidebar
                                    # (don't show if it's only one item)
        self.toctree_relations = {} # docname -> ["parent", "previous", "next"] docname
                                    # for navigating in the toctree
        self.files_to_rebuild = {}  # docname -> set of files (containing its TOCs)
                                    # to rebuild too

        # X-ref target inventory
        self.descrefs = {}          # fullname -> docname, desctype
        self.filemodules = {}       # docname -> [modules]
        self.modules = {}           # modname -> docname, synopsis, platform, deprecated
        self.labels = {}            # labelname -> docname, labelid, sectionname
        self.anonlabels = {}        # labelname -> docname, labelid
        self.reftargets = {}        # (type, name) -> docname, labelid
                                    # where type is term, token, option, envvar

        # Other inventories
        self.indexentries = {}      # docname -> list of
                                    # (type, string, target, aliasname)
        self.versionchanges = {}    # version -> list of
                                    # (type, docname, lineno, module, descname, content)

        # These are set while parsing a file
        self.docname = None         # current document name
        self.currmodule = None      # current module name
        self.currclass = None       # current class name
        self.currdesc = None        # current descref name
        self.index_num = 0          # autonumber for index targets
        self.gloss_entries = set()  # existing definition labels

        # Some magically present labels
        self.labels['genindex'] = ('genindex', '', 'Index')
        self.labels['modindex'] = ('modindex', '', 'Module Index')
        self.labels['search']   = ('search', '', 'Search Page')

    def set_warnfunc(self, func):
        self._warnfunc = func
        self.settings['warning_stream'] = RedirStream(func)

    def warn(self, docname, msg):
        if docname:
            self._warnfunc(self.doc2path(docname) + ':: ' + msg)
        else:
            self._warnfunc('GLOBAL:: ' + msg)

    def clear_doc(self, docname):
        """Remove all traces of a source file in the inventory."""
        if docname in self.all_docs:
            self.all_docs.pop(docname, None)
            self.metadata.pop(docname, None)
            self.titles.pop(docname, None)
            self.tocs.pop(docname, None)
            self.toc_num_entries.pop(docname, None)

            for subfn, fnset in self.files_to_rebuild.iteritems():
                fnset.discard(docname)
            for fullname, (fn, _) in self.descrefs.items():
                if fn == docname:
                    del self.descrefs[fullname]
            self.filemodules.pop(docname, None)
            for modname, (fn, _, _, _) in self.modules.items():
                if fn == docname:
                    del self.modules[modname]
            for labelname, (fn, _, _) in self.labels.items():
                if fn == docname:
                    del self.labels[labelname]
            for key, (fn, _) in self.reftargets.items():
                if fn == docname:
                    del self.reftargets[key]
            self.indexentries.pop(docname, None)
            for version, changes in self.versionchanges.items():
                new = [change for change in changes if change[1] != docname]
                changes[:] = new

    def doc2path(self, docname, base=True, suffix=None):
        """
        Return the filename for the document name.
        If base is True, return absolute path under self.srcdir.
        If base is None, return relative path to self.srcdir.
        If base is a path string, return absolute path under that.
        If suffix is not None, add it instead of config.source_suffix.
        """
        suffix = suffix or self.config.source_suffix
        if base is True:
            return path.join(self.srcdir, docname.replace(SEP, path.sep)) + suffix
        elif base is None:
            return docname.replace(SEP, path.sep) + suffix
        else:
            return path.join(base, docname.replace(SEP, path.sep)) + suffix

    def get_outdated_files(self, config, config_changed):
        """
        Return (added, changed, removed) sets.
        """
        self.found_docs = set(get_matching_docs(self.srcdir, config.source_suffix,
                                                exclude=set(config.unused_docs)))

        # clear all files no longer present
        removed = set(self.all_docs) - self.found_docs

        added = set()
        changed = set()

        if config_changed:
            # config values affect e.g. substitutions
            added = self.found_docs
        else:
            for docname in self.found_docs:
                if docname not in self.all_docs:
                    added.add(docname)
                else:
                    # if the doctree file is not there, rebuild
                    if not path.isfile(self.doc2path(docname, self.doctreedir, '.doctree')):
                        changed.add(docname)
                        continue
                    mtime, md5sum = self.all_docs[docname]
                    newmtime = path.getmtime(self.doc2path(docname))
                    if newmtime == mtime:
                        continue
                    changed.add(docname)

        return added, changed, removed

    def update(self, config, app=None):
        """(Re-)read all files new or changed since last update.  Yields a summary
        and then docnames as it processes them.  Store all environment docnames
        in the canonical format (ie using SEP as a separator in place of
        os.path.sep)."""
        config_changed = False
        if self.config is None:
            msg = '[new config] '
            config_changed = True
        else:
            # check if a config value was changed that affects how doctrees are read
            for key, descr in config.config_values.iteritems():
                if not descr[1]:
                    continue
                if not hasattr(self.config, key) or \
                   self.config[key] != config[key]:
                    msg = '[config changed] '
                    config_changed = True
                    break
            else:
                msg = ''
        added, changed, removed = self.get_outdated_files(config, config_changed)
        msg += '%s added, %s changed, %s removed' % (len(added), len(changed),
                                                     len(removed))
        yield msg

        self.config = config

        # clear all files no longer present
        for docname in removed:
            self.clear_doc(docname)

        # read all new and changed files
        for docname in sorted(added | changed):
            yield docname
            self.read_doc(docname, app=app)

        if config.master_doc not in self.all_docs:
            self.warn(None, 'master file %s not found' % self.doc2path(config.master_doc))

    # --------- SINGLE FILE BUILDING -------------------------------------------

    def read_doc(self, docname, src_path=None, save_parsed=True, app=None):
        """Parse a file and add/update inventory entries for the doctree.
        If srcpath is given, read from a different source file."""
        # remove all inventory entries for that file
        self.clear_doc(docname)

        if src_path is None:
            src_path = self.doc2path(docname)

        self.docname = docname
        doctree = publish_doctree(None, src_path, FileInput,
                                  settings_overrides=self.settings,
                                  reader=MyStandaloneReader())
        self.process_metadata(docname, doctree)
        self.create_title_from(docname, doctree)
        self.note_labels_from(docname, doctree)
        self.build_toc_from(docname, doctree)

        # calculate the MD5 of the file at time of build
        f = open(src_path, 'rb')
        try:
            md5sum = md5(f.read()).digest()
        finally:
            f.close()
        self.all_docs[docname] = (path.getmtime(src_path), md5sum)

        if app:
            app.emit('doctree-read', doctree)

        # make it picklable
        doctree.reporter = None
        doctree.transformer = None
        doctree.settings.warning_stream = None
        doctree.settings.env = None

        # cleanup
        self.docname = None
        self.currmodule = None
        self.currclass = None
        self.indexnum = 0
        self.gloss_entries = set()

        if save_parsed:
            # save the parsed doctree
            doctree_filename = self.doc2path(docname, self.doctreedir, '.doctree')
            dirname = path.dirname(doctree_filename)
            if not path.isdir(dirname):
                os.makedirs(dirname)
            f = open(doctree_filename, 'wb')
            try:
                pickle.dump(doctree, f, pickle.HIGHEST_PROTOCOL)
            finally:
                f.close()
        else:
            return doctree

    def process_metadata(self, docname, doctree):
        """
        Process the docinfo part of the doctree as metadata.
        """
        self.metadata[docname] = md = {}
        docinfo = doctree[0]
        if docinfo.__class__ is not nodes.docinfo:
            # nothing to see here
            return
        for node in docinfo:
            if node.__class__ is nodes.author:
                # handled specially by docutils
                md['author'] = node.astext()
            elif node.__class__ is nodes.field:
                name, body = node
                md[name.astext()] = body.astext()
        del doctree[0]

    def create_title_from(self, docname, document):
        """
        Add a title node to the document (just copy the first section title),
        and store that title in the environment.
        """
        for node in document.traverse(nodes.section):
            titlenode = nodes.title()
            visitor = MyContentsFilter(document)
            node[0].walkabout(visitor)
            titlenode += visitor.get_entry_text()
            self.titles[docname] = titlenode
            return

    def note_labels_from(self, docname, document):
        for name, explicit in document.nametypes.iteritems():
            if not explicit:
                continue
            labelid = document.nameids[name]
            node = document.ids[labelid]
            if name.isdigit() or node.has_key('refuri') or \
                   node.tagname.startswith('desc_'):
                # ignore footnote labels, labels automatically generated from a
                # link and description units
                continue
            if name in self.labels:
                self.warn(docname, 'duplicate label %s, ' % name +
                          'other instance in %s' % self.doc2path(self.labels[name][0]))
            self.anonlabels[name] = docname, labelid
            if not isinstance(node, nodes.section):
                # anonymous-only labels
                continue
            sectname = node[0].astext() # node[0] == title node
            self.labels[name] = docname, labelid, sectname

    def note_toctree(self, docname, toctreenode):
        """Note a TOC tree directive in a document and gather information about
           file relations from it."""
        includefiles = toctreenode['includefiles']
        includefiles_len = len(includefiles)
        for i, includefile in enumerate(includefiles):
            # the "previous" file for the first toctree item is the parent
            previous = i > 0 and includefiles[i-1] or docname
            # the "next" file for the last toctree item is the parent again
            next = i < includefiles_len-1 and includefiles[i+1] or docname
            self.toctree_relations[includefile] = [docname, previous, next]
            # note that if the included file is rebuilt, this one must be
            # too (since the TOC of the included file could have changed)
            self.files_to_rebuild.setdefault(includefile, set()).add(docname)


    def build_toc_from(self, docname, document):
        """Build a TOC from the doctree and store it in the inventory."""
        numentries = [0] # nonlocal again...

        def build_toc(node):
            entries = []
            for subnode in node:
                if isinstance(subnode, addnodes.toctree):
                    # just copy the toctree node which is then resolved
                    # in self.get_and_resolve_doctree
                    item = subnode.copy()
                    entries.append(item)
                    # do the inventory stuff
                    self.note_toctree(docname, subnode)
                    continue
                if not isinstance(subnode, nodes.section):
                    continue
                title = subnode[0]
                # copy the contents of the section title, but without references
                # and unnecessary stuff
                visitor = MyContentsFilter(document)
                title.walkabout(visitor)
                nodetext = visitor.get_entry_text()
                if not numentries[0]:
                    # for the very first toc entry, don't add an anchor
                    # as it is the file's title anyway
                    anchorname = ''
                else:
                    anchorname = '#' + subnode['ids'][0]
                numentries[0] += 1
                reference = nodes.reference('', '', refuri=docname,
                                            anchorname=anchorname,
                                            *nodetext)
                para = addnodes.compact_paragraph('', '', reference)
                item = nodes.list_item('', para)
                item += build_toc(subnode)
                entries.append(item)
            if entries:
                return nodes.bullet_list('', *entries)
            return []
        toc = build_toc(document)
        if toc:
            self.tocs[docname] = toc
        else:
            self.tocs[docname] = nodes.bullet_list('')
        self.toc_num_entries[docname] = numentries[0]

    def get_toc_for(self, docname):
        """Return a TOC nodetree -- for use on the same page only!"""
        toc = self.tocs[docname].deepcopy()
        for node in toc.traverse(nodes.reference):
            node['refuri'] = node['anchorname']
        return toc

    # -------
    # these are called from docutils directives and therefore use self.docname
    #
    def note_descref(self, fullname, desctype):
        if fullname in self.descrefs:
            self.warn(self.docname,
                      'duplicate canonical description name %s, ' % fullname +
                      'other instance in %s' % self.doc2path(self.descrefs[fullname][0]))
        self.descrefs[fullname] = (self.docname, desctype)

    def note_module(self, modname, synopsis, platform, deprecated):
        self.modules[modname] = (self.docname, synopsis, platform, deprecated)
        self.filemodules.setdefault(self.docname, []).append(modname)

    def note_reftarget(self, type, name, labelid):
        self.reftargets[type, name] = (self.docname, labelid)

    def note_index_entry(self, type, string, targetid, aliasname):
        self.indexentries.setdefault(self.docname, []).append(
            (type, string, targetid, aliasname))

    def note_versionchange(self, type, version, node, lineno):
        self.versionchanges.setdefault(version, []).append(
            (type, self.docname, lineno, self.currmodule, self.currdesc, node.astext()))
    # -------

    # --------- RESOLVING REFERENCES AND TOCTREES ------------------------------

    def get_doctree(self, docname):
        """Read the doctree for a file from the pickle and return it."""
        doctree_filename = self.doc2path(docname, self.doctreedir, '.doctree')
        f = open(doctree_filename, 'rb')
        try:
            doctree = pickle.load(f)
        finally:
            f.close()
        doctree.reporter = Reporter(self.doc2path(docname), 2, 4,
                                    stream=RedirStream(self._warnfunc))
        return doctree

    def get_and_resolve_doctree(self, docname, builder, doctree=None):
        """Read the doctree from the pickle, resolve cross-references and
           toctrees and return it."""
        if doctree is None:
            doctree = self.get_doctree(docname)

        # resolve all pending cross-references
        self.resolve_references(doctree, docname, builder)

        # now, resolve all toctree nodes
        def _entries_from_toctree(toctreenode):
            """Return TOC entries for a toctree node."""
            includefiles = map(str, toctreenode['includefiles'])

            entries = []
            for includefile in includefiles:
                try:
                    toc = self.tocs[includefile].deepcopy()
                except KeyError:
                    # this is raised if the included file does not exist
                    self.warn(docname, 'toctree contains ref to nonexisting '
                              'file %r' % includefile)
                else:
                    for toctreenode in toc.traverse(addnodes.toctree):
                        toctreenode.parent.replace_self(
                            _entries_from_toctree(toctreenode))
                    entries.append(toc)
            if entries:
                return addnodes.compact_paragraph('', '', *entries)
            return None

        for toctreenode in doctree.traverse(addnodes.toctree):
            maxdepth = toctreenode.get('maxdepth', -1)
            newnode = _entries_from_toctree(toctreenode)
            if newnode is not None:
                # prune the tree to maxdepth
                if maxdepth > 0:
                    walk_depth(newnode, 1, maxdepth)
                toctreenode.replace_self(newnode)
            else:
                toctreenode.replace_self([])

        # set the target paths in the toctrees (they are not known
        # at TOC generation time)
        for node in doctree.traverse(nodes.reference):
            if node.hasattr('anchorname'):
                # a TOC reference
                node['refuri'] = builder.get_relative_uri(
                    docname, node['refuri']) + node['anchorname']

        return doctree


    descroles = frozenset(('data', 'exc', 'func', 'class', 'const', 'attr',
                           'meth', 'cfunc', 'cdata', 'ctype', 'cmacro'))

    def resolve_references(self, doctree, fromdocname, builder):
        for node in doctree.traverse(addnodes.pending_xref):
            contnode = node[0].deepcopy()
            newnode = None

            typ = node['reftype']
            target = node['reftarget']

            reftarget_roles = set(('token', 'term', 'option'))
            # add all custom xref types too
            reftarget_roles.update(i[0] for i in additional_xref_types.values())

            try:
                if typ == 'ref':
                    if node['refcaption']:
                        # reference to anonymous label; the reference uses the supplied
                        # link caption
                        docname, labelid = self.anonlabels.get(target, ('',''))
                        sectname = node.astext()
                        if not docname:
                            newnode = doctree.reporter.system_message(
                                2, 'undefined label: %s' % target)
                    else:
                        # reference to the named label; the final node will contain the
                        # section name after the label
                        docname, labelid, sectname = self.labels.get(target, ('','',''))
                        if not docname:
                            newnode = doctree.reporter.system_message(
                                2, 'undefined label: %s -- if you don\'t ' % target +
                                'give a link caption the label must precede a section '
                                'header.')
                    if docname:
                        newnode = nodes.reference('', '')
                        innernode = nodes.emphasis(sectname, sectname)
                        if docname == fromdocname:
                            newnode['refid'] = labelid
                        else:
                            # set more info in contnode in case the get_relative_uri call
                            # raises NoUri, the builder will then have to resolve these
                            contnode = addnodes.pending_xref('')
                            contnode['refdocname'] = docname
                            contnode['refsectname'] = sectname
                            newnode['refuri'] = builder.get_relative_uri(
                                fromdocname, docname)
                            if labelid:
                                newnode['refuri'] += '#' + labelid
                        newnode.append(innernode)
                elif typ == 'keyword':
                    # keywords are referenced by named labels
                    docname, labelid, _ = self.labels.get(target, ('','',''))
                    if not docname:
                        self.warn(fromdocname, 'unknown keyword: %s' % target)
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if docname == fromdocname:
                            newnode['refid'] = labelid
                        else:
                            newnode['refuri'] = builder.get_relative_uri(
                                fromdocname, docname) + '#' + labelid
                        newnode.append(contnode)
                elif typ in reftarget_roles:
                    docname, labelid = self.reftargets.get((typ, target), ('', ''))
                    if not docname:
                        if typ == 'term':
                            self.warn(fromdocname, 'term not in glossary: %s' % target)
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if docname == fromdocname:
                            newnode['refid'] = labelid
                        else:
                            newnode['refuri'] = builder.get_relative_uri(
                                fromdocname, docname, typ) + '#' + labelid
                        newnode.append(contnode)
                elif typ == 'mod':
                    docname, synopsis, platform, deprecated = \
                        self.modules.get(target, ('','','', ''))
                    # just link to an anchor if there are multiple modules in one file
                    # because the anchor is generally below the heading which is ugly
                    # but can't be helped easily
                    anchor = ''
                    if not docname or docname == fromdocname:
                        # don't link to self
                        newnode = contnode
                    else:
                        if len(self.filemodules[docname]) > 1:
                            anchor = '#' + 'module-' + target
                        newnode = nodes.reference('', '')
                        newnode['refuri'] = (
                            builder.get_relative_uri(fromdocname, docname) + anchor)
                        newnode['reftitle'] = '%s%s%s' % (
                            (platform and '(%s) ' % platform),
                            synopsis, (deprecated and ' (deprecated)' or ''))
                        newnode.append(contnode)
                elif typ in self.descroles:
                    # "descrefs"
                    modname = node['modname']
                    clsname = node['classname']
                    searchorder = node.hasattr('refspecific') and 1 or 0
                    name, desc = self.find_desc(modname, clsname,
                                                target, typ, searchorder)
                    if not desc:
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if desc[0] == fromdocname:
                            newnode['refid'] = name
                        else:
                            newnode['refuri'] = (
                                builder.get_relative_uri(fromdocname, desc[0])
                                + '#' + name)
                        newnode.append(contnode)
                else:
                    raise RuntimeError('unknown xfileref node encountered: %s' % node)
            except NoUri:
                newnode = contnode
            if newnode:
                node.replace_self(newnode)

        # allow custom references to be resolved
        builder.app.emit('doctree-resolved', doctree, fromdocname)

    def create_index(self, builder, _fixre=re.compile(r'(.*) ([(][^()]*[)])')):
        """Create the real index from the collected index entries."""
        new = {}

        def add_entry(word, subword, dic=new):
            entry = dic.get(word)
            if not entry:
                dic[word] = entry = [[], {}]
            if subword:
                add_entry(subword, '', dic=entry[1])
            else:
                try:
                    entry[0].append(builder.get_relative_uri('genindex', fn)
                                    + '#' + tid)
                except NoUri:
                    pass

        for fn, entries in self.indexentries.iteritems():
            # new entry types must be listed in directives.py!
            for type, string, tid, alias in entries:
                if type == 'single':
                    try:
                        entry, subentry = string.split(';', 1)
                    except:
                        entry, subentry = string, ''
                    add_entry(entry.strip(), subentry.strip())
                elif type == 'pair':
                    first, second = map(lambda x: x.strip(), string.split(';', 1))
                    add_entry(first, second)
                    add_entry(second, first)
                elif type == 'triple':
                    first, second, third = map(lambda x: x.strip(), string.split(';', 2))
                    add_entry(first, second+' '+third)
                    add_entry(second, third+', '+first)
                    add_entry(third, first+' '+second)
                elif type in ('module', 'keyword', 'operator', 'object',
                              'exception', 'statement'):
                    add_entry(string, type)
                    add_entry(type, string)
                elif type == 'builtin':
                    add_entry(string, 'built-in function')
                    add_entry('built-in function', string)
                else:
                    self.warn(fn, "unknown index entry type %r" % type)

        newlist = new.items()
        newlist.sort(key=lambda t: t[0].lower())

        # fixup entries: transform
        #   func() (in module foo)
        #   func() (in module bar)
        # into
        #   func()
        #     (in module foo)
        #     (in module bar)
        oldkey = ''
        oldsubitems = None
        i = 0
        while i < len(newlist):
            key, (targets, subitems) = newlist[i]
            # cannot move if it hassubitems; structure gets too complex
            if not subitems:
                m = _fixre.match(key)
                if m:
                    if oldkey == m.group(1):
                        # prefixes match: add entry as subitem of the previous entry
                        oldsubitems.setdefault(m.group(2), [[], {}])[0].extend(targets)
                        del newlist[i]
                        continue
                    oldkey = m.group(1)
                else:
                    oldkey = key
            oldsubitems = subitems
            i += 1

        # group the entries by letter
        def keyfunc((k, v), ltrs=uppercase+'_'):
            # hack: mutate the subitems dicts to a list in the keyfunc
            v[1] = sorted((si, se) for (si, (se, void)) in v[1].iteritems())
            # now calculate the key
            letter = k[0].upper()
            if letter in ltrs:
                return letter
            else:
                # get all other symbols under one heading
                return 'Symbols'
        self.index = [(key, list(group)) for (key, group) in
                      itertools.groupby(newlist, keyfunc)]

    def check_consistency(self):
        """Do consistency checks."""

        for docname in self.all_docs:
            if docname not in self.toctree_relations:
                if docname == self.config.master_doc:
                    # the master file is not included anywhere ;)
                    continue
                self.warn(docname, 'document isn\'t included in any toctree')

    # --------- QUERYING -------------------------------------------------------

    def find_desc(self, modname, classname, name, type, searchorder=0):
        """Find a description node matching "name", perhaps using
           the given module and/or classname."""
        # skip parens
        if name[-2:] == '()':
            name = name[:-2]

        if not name:
            return None, None

        # don't add module and class names for C things
        if type[0] == 'c' and type not in ('class', 'const'):
            # skip trailing star and whitespace
            name = name.rstrip(' *')
            if name in self.descrefs and self.descrefs[name][1][0] == 'c':
                return name, self.descrefs[name]
            return None, None

        newname = None
        if searchorder == 1:
            if modname and classname and \
                   modname + '.' + classname + '.' + name in self.descrefs:
                newname = modname + '.' + classname + '.' + name
            elif modname and modname + '.' + name in self.descrefs:
                newname = modname + '.' + name
            elif name in self.descrefs:
                newname = name
        else:
            if name in self.descrefs:
                newname = name
            elif modname and modname + '.' + name in self.descrefs:
                newname = modname + '.' + name
            elif modname and classname and \
                     modname + '.' + classname + '.' + name in self.descrefs:
                newname = modname + '.' + classname + '.' + name
            # special case: builtin exceptions have module "exceptions" set
            elif type == 'exc' and '.' not in name and \
                 'exceptions.' + name in self.descrefs:
                newname = 'exceptions.' + name
            # special case: object methods
            elif type in ('func', 'meth') and '.' not in name and \
                 'object.' + name in self.descrefs:
                newname = 'object.' + name
        if newname is None:
            return None, None
        return newname, self.descrefs[newname]

    def find_keyword(self, keyword, avoid_fuzzy=False, cutoff=0.6, n=20):
        """
        Find keyword matches for a keyword. If there's an exact match, just return
        it, else return a list of fuzzy matches if avoid_fuzzy isn't True.

        Keywords searched are: first modules, then descrefs.

        Returns: None if nothing found
                 (type, docname, anchorname) if exact match found
                 list of (quality, type, docname, anchorname, description) if fuzzy
        """

        if keyword in self.modules:
            docname, title, system, deprecated = self.modules[keyword]
            return 'module', docname, 'module-' + keyword
        if keyword in self.descrefs:
            docname, ref_type = self.descrefs[keyword]
            return ref_type, docname, keyword
        # special cases
        if '.' not in keyword:
            # exceptions are documented in the exceptions module
            if 'exceptions.'+keyword in self.descrefs:
                docname, ref_type = self.descrefs['exceptions.'+keyword]
                return ref_type, docname, 'exceptions.'+keyword
            # special methods are documented as object methods
            if 'object.'+keyword in self.descrefs:
                docname, ref_type = self.descrefs['object.'+keyword]
                return ref_type, docname, 'object.'+keyword

        if avoid_fuzzy:
            return

        # find fuzzy matches
        s = difflib.SequenceMatcher()
        s.set_seq2(keyword.lower())

        def possibilities():
            for title, (fn, desc, _, _) in self.modules.iteritems():
                yield ('module', fn, 'module-'+title, desc)
            for title, (fn, desctype) in self.descrefs.iteritems():
                yield (desctype, fn, title, '')

        def dotsearch(string):
            parts = string.lower().split('.')
            for idx in xrange(0, len(parts)):
                yield '.'.join(parts[idx:])

        result = []
        for type, docname, title, desc in possibilities():
            best_res = 0
            for part in dotsearch(title):
                s.set_seq1(part)
                if s.real_quick_ratio() >= cutoff and \
                   s.quick_ratio() >= cutoff and \
                   s.ratio() >= cutoff and \
                   s.ratio() > best_res:
                    best_res = s.ratio()
            if best_res:
                result.append((best_res, type, docname, title, desc))

        return heapq.nlargest(n, result)
