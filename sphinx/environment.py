# -*- coding: utf-8 -*-
"""
    sphinx.environment
    ~~~~~~~~~~~~~~~~~~

    Global creation environment.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""
from __future__ import with_statement

import re
import os
import time
import heapq
import hashlib
import difflib
import itertools
import cPickle as pickle
from os import path
from string import uppercase

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

from . import addnodes
from .util import get_matching_files, os_path, SEP
from .refcounting import Refcounts

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
ENV_VERSION = 13


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
                text = config.get(refname, '')
                if refname == 'today' and not text:
                    # special handling: can also specify a strftime format
                    text = time.strftime(config.get('today_fmt', '%B %d, %Y'))
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
    Add our own Substitutions transform.
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
        with open(filename, 'rb') as picklefile:
            env = pickle.load(picklefile)
        if env.version != ENV_VERSION:
            raise IOError('env version not current')
        return env

    def topickle(self, filename):
        # remove unpicklable attributes
        wstream = self.warning_stream
        self.set_warning_stream(None)
        with open(filename, 'wb') as picklefile:
            pickle.dump(self, picklefile, pickle.HIGHEST_PROTOCOL)
        # reset stream
        self.set_warning_stream(wstream)

    # --------- ENVIRONMENT INITIALIZATION -------------------------------------

    def __init__(self, srcdir, doctreedir):
        self.doctreedir = doctreedir
        self.srcdir = srcdir
        self.config = {}

        # read the refcounts file
        self.refcounts = Refcounts.fromfile(
            path.join(self.srcdir, 'data', 'refcounts.dat'))

        # the docutils settings for building
        self.settings = default_settings.copy()
        self.settings['env'] = self

        # the stream to write warning messages to
        self.warning_stream = None

        # this is to invalidate old pickles
        self.version = ENV_VERSION

        # Build times -- to determine changed files
        # Also use this as an inventory of all existing and built filenames.
        self.all_files = {}         # filename -> (mtime, md5) at the time of build

        # File metadata
        self.metadata = {}          # filename -> dict of metadata items

        # TOC inventory
        self.titles = {}            # filename -> title node
        self.tocs = {}              # filename -> table of contents nodetree
        self.toc_num_entries = {}   # filename -> number of real entries
                                    # used to determine when to show the TOC in a sidebar
                                    # (don't show if it's only one item)
        self.toctree_relations = {} # filename -> ["parent", "previous", "next"] filename
                                    # for navigating in the toctree
        self.files_to_rebuild = {}  # filename -> set of files (containing its TOCs)
                                    # to rebuild too

        # X-ref target inventory
        self.descrefs = {}          # fullname -> filename, desctype
        self.filemodules = {}       # filename -> [modules]
        self.modules = {}           # modname -> filename, synopsis, platform, deprecated
        self.labels = {}            # labelname -> filename, labelid, sectionname
        self.reftargets = {}        # (type, name) -> filename, labelid
                                    # where type is term, token, option, envvar

        # Other inventories
        self.indexentries = {}      # filename -> list of
                                    # (type, string, target, aliasname)
        self.versionchanges = {}    # version -> list of
                                    # (type, filename, module, descname, content)

        # These are set while parsing a file
        self.filename = None        # current file name
        self.currmodule = None      # current module name
        self.currclass = None       # current class name
        self.currdesc = None        # current descref name
        self.index_num = 0          # autonumber for index targets
        self.gloss_entries = set()  # existing definition labels

    def set_warning_stream(self, stream):
        self.warning_stream = stream
        self.settings['warning_stream'] = stream

    def clear_file(self, filename):
        """Remove all traces of a source file in the inventory."""
        if filename in self.all_files:
            self.all_files.pop(filename, None)
            self.metadata.pop(filename, None)
            self.titles.pop(filename, None)
            self.tocs.pop(filename, None)
            self.toc_num_entries.pop(filename, None)

            for subfn, fnset in self.files_to_rebuild.iteritems():
                fnset.discard(filename)
            for fullname, (fn, _) in self.descrefs.items():
                if fn == filename:
                    del self.descrefs[fullname]
            self.filemodules.pop(filename, None)
            for modname, (fn, _, _, _) in self.modules.items():
                if fn == filename:
                    del self.modules[modname]
            for labelname, (fn, _, _) in self.labels.items():
                if fn == filename:
                    del self.labels[labelname]
            for key, (fn, _) in self.reftargets.items():
                if fn == filename:
                    del self.reftargets[key]
            self.indexentries.pop(filename, None)
            for version, changes in self.versionchanges.items():
                new = [change for change in changes if change[1] != filename]
                changes[:] = new

    def get_outdated_files(self, config):
        """
        Return (added, changed, removed) iterables.
        """
        all_source_files = list(get_matching_files(
            self.srcdir, '*.rst', exclude=set(config.get('unused_files', ()))))

        # clear all files no longer present
        removed = set(self.all_files) - set(all_source_files)

        added = []
        changed = []

        if config != self.config:
            # config values affect e.g. substitutions
            added = all_source_files
        else:
            for filename in all_source_files:
                if filename not in self.all_files:
                    added.append(filename)
                else:
                    # if the doctree file is not there, rebuild
                    if not path.isfile(path.join(self.doctreedir,
                                                 os_path(filename)[:-3] + 'doctree')):
                        changed.append(filename)
                        continue
                    mtime, md5 = self.all_files[filename]
                    newmtime = path.getmtime(path.join(self.srcdir, os_path(filename)))
                    if newmtime == mtime:
                        continue
                    # check the MD5
                    #with file(path.join(self.srcdir, filename), 'rb') as f:
                    #    newmd5 = hashlib.md5(f.read()).digest()
                    #if newmd5 != md5:
                    changed.append(filename)

        return added, changed, removed

    def update(self, config):
        """
        (Re-)read all files new or changed since last update.
        Yields a summary and then filenames as it processes them.
        Store all environment filenames in the canonical format
        (ie using SEP as a separator in place of os.path.sep).
        """
        added, changed, removed = self.get_outdated_files(config)
        msg = '%s added, %s changed, %s removed' % (len(added), len(changed),
                                                    len(removed))
        if self.config != config:
            msg = '[config changed] ' + msg
        yield msg

        self.config = config

        # clear all files no longer present
        for filename in removed:
            self.clear_file(filename)

        # re-read the refcount file
        self.refcounts = Refcounts.fromfile(
            path.join(self.srcdir, 'data', 'refcounts.dat'))

        # read all new and changed files
        for filename in added + changed:
            yield filename
            self.read_file(filename)

    # --------- SINGLE FILE BUILDING -------------------------------------------

    def read_file(self, filename, src_path=None, save_parsed=True):
        """Parse a file and add/update inventory entries for the doctree.
        If srcpath is given, read from a different source file."""
        # remove all inventory entries for that file
        self.clear_file(filename)

        if src_path is None:
            src_path = path.join(self.srcdir, os_path(filename))

        self.filename = filename
        doctree = publish_doctree(None, src_path, FileInput,
                                  settings_overrides=self.settings,
                                  reader=MyStandaloneReader())
        self.process_metadata(filename, doctree)
        self.create_title_from(filename, doctree)
        self.note_labels_from(filename, doctree)
        self.build_toc_from(filename, doctree)

        # calculate the MD5 of the file at time of build
        with file(src_path, 'rb') as f:
            md5 = hashlib.md5(f.read()).digest()
        self.all_files[filename] = (path.getmtime(src_path), md5)

        # make it picklable
        doctree.reporter = None
        doctree.transformer = None
        doctree.settings.env = None
        doctree.settings.warning_stream = None

        # cleanup
        self.filename = None
        self.currmodule = None
        self.currclass = None
        self.indexnum = 0
        self.gloss_entries = set()

        if save_parsed:
            # save the parsed doctree
            doctree_filename = path.join(self.doctreedir, os_path(filename)[:-3] + 'doctree')
            dirname = path.dirname(doctree_filename)
            if not path.isdir(dirname):
                os.makedirs(dirname)
            with file(doctree_filename, 'wb') as f:
                pickle.dump(doctree, f, pickle.HIGHEST_PROTOCOL)
        else:
            return doctree

    def process_metadata(self, filename, doctree):
        """
        Process the docinfo part of the doctree as metadata.
        """
        self.metadata[filename] = md = {}
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

    def create_title_from(self, filename, document):
        """
        Add a title node to the document (just copy the first section title),
        and store that title in the environment.
        """
        for node in document.traverse(nodes.section):
            titlenode = nodes.title()
            visitor = MyContentsFilter(document)
            node[0].walkabout(visitor)
            titlenode += visitor.get_entry_text()
            self.titles[filename] = titlenode
            return

    def note_labels_from(self, filename, document):
        for name, explicit in document.nametypes.iteritems():
            if not explicit:
                continue
            labelid = document.nameids[name]
            node = document.ids[labelid]
            if not isinstance(node, nodes.section):
                # e.g. desc-signatures
                continue
            sectname = node[0].astext() # node[0] == title node
            if name in self.labels:
                print >>self.warning_stream, \
                      ('WARNING: duplicate label %s, ' % name +
                       'in %s and %s' % (self.labels[name][0], filename))
            self.labels[name] = filename, labelid, sectname

    def note_toctree(self, filename, toctreenode):
        """Note a TOC tree directive in a document and gather information about
           file relations from it."""
        includefiles = toctreenode['includefiles']
        includefiles_len = len(includefiles)
        for i, includefile in enumerate(includefiles):
            # the "previous" file for the first toctree item is the parent
            previous = includefiles[i-1] if i > 0 else filename
            # the "next" file for the last toctree item is the parent again
            next = includefiles[i+1] if i < includefiles_len-1 else filename
            self.toctree_relations[includefile] = [filename, previous, next]
            # note that if the included file is rebuilt, this one must be
            # too (since the TOC of the included file could have changed)
            self.files_to_rebuild.setdefault(includefile, set()).add(filename)


    def build_toc_from(self, filename, document):
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
                    self.note_toctree(filename, subnode)
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
                reference = nodes.reference('', '', refuri=filename,
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
            self.tocs[filename] = toc
        else:
            self.tocs[filename] = nodes.bullet_list('')
        self.toc_num_entries[filename] = numentries[0]

    def get_toc_for(self, filename):
        """Return a TOC nodetree -- for use on the same page only!"""
        toc = self.tocs[filename].deepcopy()
        for node in toc.traverse(nodes.reference):
            node['refuri'] = node['anchorname']
        return toc

    # -------
    # these are called from docutils directives and therefore use self.filename
    #
    def note_descref(self, fullname, desctype):
        if fullname in self.descrefs:
            print >>self.warning_stream, \
                  ('WARNING: duplicate canonical description name %s, ' % fullname +
                   'in %s and %s' % (self.descrefs[fullname][0], self.filename))
        self.descrefs[fullname] = (self.filename, desctype)

    def note_module(self, modname, synopsis, platform, deprecated):
        self.modules[modname] = (self.filename, synopsis, platform, deprecated)
        self.filemodules.setdefault(self.filename, []).append(modname)

    def note_reftarget(self, type, name, labelid):
        self.reftargets[type, name] = (self.filename, labelid)

    def note_index_entry(self, type, string, targetid, aliasname):
        self.indexentries.setdefault(self.filename, []).append(
            (type, string, targetid, aliasname))

    def note_versionchange(self, type, version, node):
        self.versionchanges.setdefault(version, []).append(
            (type, self.filename, self.currmodule, self.currdesc, node.deepcopy()))
    # -------

    # --------- RESOLVING REFERENCES AND TOCTREES ------------------------------

    def get_doctree(self, filename):
        """Read the doctree for a file from the pickle and return it."""
        doctree_filename = path.join(self.doctreedir, os_path(filename)[:-3] + 'doctree')
        with file(doctree_filename, 'rb') as f:
            doctree = pickle.load(f)
        doctree.reporter = Reporter(filename, 2, 4, stream=self.warning_stream)
        return doctree

    def get_and_resolve_doctree(self, filename, builder, doctree=None):
        """Read the doctree from the pickle, resolve cross-references and
           toctrees and return it."""
        if doctree is None:
            doctree = self.get_doctree(filename)

        # resolve all pending cross-references
        self.resolve_references(doctree, filename, builder)

        # now, resolve all toctree nodes
        def _entries_from_toctree(toctreenode):
            """Return TOC entries for a toctree node."""
            includefiles = map(str, toctreenode['includefiles'])

            entries = []
            for includefile in includefiles:
                try:
                    toc = self.tocs[includefile].deepcopy()
                except KeyError, err:
                    # this is raised if the included file does not exist
                    print >>self.warning_stream, 'WARNING: %s: toctree contains ' \
                          'ref to nonexisting file %r' % (filename, includefile)
                else:
                    for toctreenode in toc.traverse(addnodes.toctree):
                        toctreenode.parent.replace_self(
                            _entries_from_toctree(toctreenode))
                    entries.append(toc)
            if entries:
                return addnodes.compact_paragraph('', '', *entries)
            return []

        for toctreenode in doctree.traverse(addnodes.toctree):
            maxdepth = toctreenode.get('maxdepth', -1)
            newnode = _entries_from_toctree(toctreenode)
            # prune the tree to maxdepth
            if maxdepth > 0:
                walk_depth(newnode, 1, maxdepth)
            toctreenode.replace_self(newnode)

        # set the target paths in the toctrees (they are not known
        # at TOC generation time)
        for node in doctree.traverse(nodes.reference):
            if node.hasattr('anchorname'):
                # a TOC reference
                node['refuri'] = builder.get_relative_uri(
                    filename, node['refuri']) + node['anchorname']

        return doctree


    def resolve_references(self, doctree, docfilename, builder):
        for node in doctree.traverse(addnodes.pending_xref):
            contnode = node[0].deepcopy()
            newnode = None

            typ = node['reftype']
            target = node['reftarget']

            try:
                if typ == 'ref':
                    filename, labelid, sectname = self.labels.get(target, ('','',''))
                    if not filename:
                        newnode = doctree.reporter.system_message(
                            2, 'undefined label: %s' % target)
                        print >>self.warning_stream, \
                              '%s: undefined label: %s' % (docfilename, target)
                    else:
                        newnode = nodes.reference('', '')
                        innernode = nodes.emphasis(sectname, sectname)
                        if filename == docfilename:
                            newnode['refid'] = labelid
                        else:
                            # in case the following calls raises NoUri...
                            # else the final node will contain a label name
                            contnode = innernode
                            newnode['refuri'] = builder.get_relative_uri(
                                docfilename, filename) + '#' + labelid
                        newnode.append(innernode)
                elif typ in ('token', 'term', 'envvar', 'option'):
                    filename, labelid = self.reftargets.get((typ, target), ('', ''))
                    if not filename:
                        if typ == 'term':
                            print >>self.warning_stream, \
                                  '%s: term not in glossary: %s' % (docfilename, target)
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if filename == docfilename:
                            newnode['refid'] = labelid
                        else:
                            newnode['refuri'] = builder.get_relative_uri(
                                docfilename, filename, typ) + '#' + labelid
                        newnode.append(contnode)
                elif typ == 'mod':
                    filename, synopsis, platform, deprecated = \
                        self.modules.get(target, ('','','', ''))
                    # just link to an anchor if there are multiple modules in one file
                    # because the anchor is generally below the heading which is ugly
                    # but can't be helped easily
                    anchor = ''
                    if not filename or filename == docfilename:
                        # don't link to self
                        newnode = contnode
                    else:
                        if len(self.filemodules[filename]) > 1:
                            anchor = '#' + 'module-' + target
                        newnode = nodes.reference('', '')
                        newnode['refuri'] = (
                            builder.get_relative_uri(docfilename, filename) + anchor)
                        newnode['reftitle'] = '%s%s%s' % (
                            ('(%s) ' % platform if platform else ''),
                            synopsis, (' (deprecated)' if deprecated else ''))
                        newnode.append(contnode)
                else:
                    modname = node['modname']
                    clsname = node['classname']
                    searchorder = 1 if node.hasattr('refspecific') else 0
                    name, desc = self.find_desc(modname, clsname, target, typ, searchorder)
                    if not desc:
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if desc[0] == docfilename:
                            newnode['refid'] = name
                        else:
                            newnode['refuri'] = (
                                builder.get_relative_uri(docfilename, desc[0])
                                + '#' + name)
                        newnode.append(contnode)
            except NoUri:
                newnode = contnode
            if newnode:
                node.replace_self(newnode)

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
                    entry[0].append(builder.get_relative_uri('genindex.rst', fn)
                                    + '#' + tid)
                except NoUri:
                    pass

        for fn, entries in self.indexentries.iteritems():
            # new entry types must be listed in directives.py!
            for type, string, tid, alias in entries:
                if type == 'single':
                    entry, _, subentry = string.partition(';')
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
                    print >>self.warning_stream, \
                          "unknown index entry type %r in %s" % (type, fn)

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

        for filename in self.all_files:
            if filename not in self.toctree_relations:
                if filename == 'contents.rst':
                    # the master file is not included anywhere ;)
                    continue
                self.warning_stream.write(
                    'WARNING: %s isn\'t included in any toctree\n' % filename)

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
                 (type, filename, anchorname) if exact match found
                 list of (quality, type, filename, anchorname, description) if fuzzy
        """

        if keyword in self.modules:
            filename, title, system, deprecated = self.modules[keyword]
            return 'module', filename, 'module-' + keyword
        if keyword in self.descrefs:
            filename, ref_type = self.descrefs[keyword]
            return ref_type, filename, keyword
        # special cases
        if '.' not in keyword:
            # exceptions are documented in the exceptions module
            if 'exceptions.'+keyword in self.descrefs:
                filename, ref_type = self.descrefs['exceptions.'+keyword]
                return ref_type, filename, 'exceptions.'+keyword
            # special methods are documented as object methods
            if 'object.'+keyword in self.descrefs:
                filename, ref_type = self.descrefs['object.'+keyword]
                return ref_type, filename, 'object.'+keyword

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
        for type, filename, title, desc in possibilities():
            best_res = 0
            for part in dotsearch(title):
                s.set_seq1(part)
                if s.real_quick_ratio() >= cutoff and \
                   s.quick_ratio() >= cutoff and \
                   s.ratio() >= cutoff and \
                   s.ratio() > best_res:
                    best_res = s.ratio()
            if best_res:
                result.append((best_res, type, filename, title, desc))

        return heapq.nlargest(n, result)

    def get_real_filename(self, filename):
        """
        Pass this function a filename without .rst extension to get the real
        filename. This also resolves the special `index.rst` files. If the file
        does not exist the return value will be `None`.
        """
        for rstname in filename + '.rst', filename + SEP + 'index.rst':
            if rstname in self.all_files:
                return rstname
