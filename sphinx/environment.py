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
import types
import imghdr
import difflib
import cPickle as pickle
from os import path
from glob import glob
from string import uppercase
from itertools import izip, groupby
try:
    import hashlib
    md5 = hashlib.md5
except ImportError:
    # 2.4 compatibility
    import md5
    md5 = md5.new

from docutils import nodes
from docutils.io import FileInput
from docutils.core import publish_doctree
from docutils.utils import Reporter
from docutils.readers import standalone
from docutils.parsers.rst import roles
from docutils.parsers.rst.languages import en as english
from docutils.transforms import Transform
from docutils.transforms.parts import ContentsFilter

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
    'rfc_base_url': 'http://rfc.net/',
    'input_encoding': 'utf-8',
    'doctitle_xform': False,
    'sectsubtitle_xform': False,
}

# This is increased every time an environment attribute is added
# or changed to properly invalidate pickle files.
ENV_VERSION = 25


default_substitutions = set([
    'version',
    'release',
    'today',
])

dummy_reporter = Reporter('', 4, 4)


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
                    text = time.strftime(config.today_fmt or _('%B %d, %Y'))
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


class HandleCodeBlocks(Transform):
    """
    Move doctest blocks out of blockquotes and connect adjacent code blocks.
    """
    default_priority = 210

    def apply(self):
        for node in self.document.traverse(nodes.block_quote):
            if len(node.children) == 1 and isinstance(node.children[0],
                                                      nodes.doctest_block):
                node.replace_self(node.children[0])


class SphinxStandaloneReader(standalone.Reader):
    """
    Add our own transforms.
    """
    transforms = [DefaultSubstitutions, MoveModuleTargets, HandleCodeBlocks]
    def get_transforms(self):
        tf = standalone.Reader.get_transforms(self)
        return tf + self.transforms


class SphinxContentsFilter(ContentsFilter):
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
    """

    # --------- ENVIRONMENT PERSISTENCE ----------------------------------------

    @staticmethod
    def frompickle(config, filename):
        picklefile = open(filename, 'rb')
        try:
            env = pickle.load(picklefile)
        finally:
            picklefile.close()
        env.config.values = config.values
        if env.version != ENV_VERSION:
            raise IOError('env version not current')
        return env

    def topickle(self, filename):
        # remove unpicklable attributes
        warnfunc = self._warnfunc
        self.set_warnfunc(None)
        values = self.config.values
        del self.config.values
        picklefile = open(filename, 'wb')
        # remove potentially pickling-problematic values from config
        for key, val in vars(self.config).items():
            if key.startswith('_') or \
                   isinstance(val, types.ModuleType) or \
                   isinstance(val, types.FunctionType) or \
                   isinstance(val, (type, types.ClassType)):
                del self.config[key]
        try:
            pickle.dump(self, picklefile, pickle.HIGHEST_PROTOCOL)
        finally:
            picklefile.close()
        # reset attributes
        self.config.values = values
        self.set_warnfunc(warnfunc)

    # --------- ENVIRONMENT INITIALIZATION -------------------------------------

    def __init__(self, srcdir, doctreedir, config):
        self.doctreedir = doctreedir
        self.srcdir = srcdir
        self.config = config

        # the application object; only set while update() runs
        self.app = None

        # the docutils settings for building
        self.settings = default_settings.copy()
        self.settings['env'] = self

        # the function to write warning messages with
        self._warnfunc = None

        # this is to invalidate old pickles
        self.version = ENV_VERSION

        # All "docnames" here are /-separated and relative and exclude the source suffix.

        self.found_docs = set()     # contains all existing docnames
        self.all_docs = {}          # docname -> mtime at the time of build
                                    # contains all built docnames
        self.dependencies = {}      # docname -> set of dependent file names, relative to
                                    # documentation root

        # File metadata
        self.metadata = {}          # docname -> dict of metadata items

        # TOC inventory
        self.titles = {}            # docname -> title node
        self.tocs = {}              # docname -> table of contents nodetree
        self.toc_num_entries = {}   # docname -> number of real entries
                                    # used to determine when to show the TOC in a sidebar
                                    # (don't show if it's only one item)
        self.toctree_includes = {}  # docname -> list of toctree includefiles
        self.files_to_rebuild = {}  # docname -> set of files (containing its TOCs)
                                    # to rebuild too
        self.glob_toctrees = set()  # docnames that have :glob: toctrees

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
        self.images = {}            # absolute path -> (docnames, unique filename)

        # These are set while parsing a file
        self.docname = None         # current document name
        self.currmodule = None      # current module name
        self.currclass = None       # current class name
        self.currdesc = None        # current descref name
        self.index_num = 0          # autonumber for index targets
        self.gloss_entries = set()  # existing definition labels

        # Some magically present labels
        self.labels['genindex'] = ('genindex', '', _('Index'))
        self.labels['modindex'] = ('modindex', '', _('Module Index'))
        self.labels['search']   = ('search', '', _('Search Page'))

    def set_warnfunc(self, func):
        self._warnfunc = func
        self.settings['warning_stream'] = RedirStream(func)

    def warn(self, docname, msg, lineno=None):
        if docname:
            if lineno is None:
                lineno = ''
            self._warnfunc('%s:%s: %s' % (self.doc2path(docname), lineno, msg))
        else:
            self._warnfunc('GLOBAL:: ' + msg)

    def clear_doc(self, docname):
        """Remove all traces of a source file in the inventory."""
        if docname in self.all_docs:
            self.all_docs.pop(docname, None)
            self.metadata.pop(docname, None)
            self.dependencies.pop(docname, None)
            self.titles.pop(docname, None)
            self.tocs.pop(docname, None)
            self.toc_num_entries.pop(docname, None)
            self.toctree_includes.pop(docname, None)
            self.filemodules.pop(docname, None)
            self.indexentries.pop(docname, None)
            self.glob_toctrees.discard(docname)

            for subfn, fnset in self.files_to_rebuild.items():
                fnset.discard(docname)
                if not fnset:
                    del self.files_to_rebuild[subfn]
            for fullname, (fn, _) in self.descrefs.items():
                if fn == docname:
                    del self.descrefs[fullname]
            for modname, (fn, _, _, _) in self.modules.items():
                if fn == docname:
                    del self.modules[modname]
            for labelname, (fn, _, _) in self.labels.items():
                if fn == docname:
                    del self.labels[labelname]
            for key, (fn, _) in self.reftargets.items():
                if fn == docname:
                    del self.reftargets[key]
            for version, changes in self.versionchanges.items():
                new = [change for change in changes if change[1] != docname]
                changes[:] = new
            for fullpath, (docs, _) in self.images.items():
                docs.discard(docname)
                if not docs:
                    del self.images[fullpath]

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

    def find_files(self, config):
        """
        Find all source files in the source dir and put them in self.found_docs.
        """
        exclude_dirs  = [d.replace(SEP, path.sep) for d in config.exclude_dirs]
        exclude_trees = [d.replace(SEP, path.sep) for d in config.exclude_trees]
        self.found_docs = set(get_matching_docs(
            self.srcdir, config.source_suffix, exclude_docs=set(config.unused_docs),
            exclude_dirs=exclude_dirs, exclude_trees=exclude_trees,
            exclude_dirnames=['_sources'] + config.exclude_dirnames))

    def get_outdated_files(self, config_changed):
        """
        Return (added, changed, removed) sets.
        """
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
                    continue
                # if the doctree file is not there, rebuild
                if not path.isfile(self.doc2path(docname, self.doctreedir,
                                                 '.doctree')):
                    changed.add(docname)
                    continue
                # check the mtime of the document
                mtime = self.all_docs[docname]
                newmtime = path.getmtime(self.doc2path(docname))
                if newmtime > mtime:
                    changed.add(docname)
                    continue
                # finally, check the mtime of dependencies
                for dep in self.dependencies.get(docname, ()):
                    try:
                        # this will do the right thing when dep is absolute too
                        deppath = path.join(self.srcdir, dep)
                        if not path.isfile(deppath):
                            changed.add(docname)
                            break
                        depmtime = path.getmtime(deppath)
                        if depmtime > mtime:
                            changed.add(docname)
                            break
                    except EnvironmentError:
                        # give it another chance
                        changed.add(docname)
                        break

        return added, changed, removed

    def update(self, config, srcdir, doctreedir, app=None):
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
                if self.config[key] != config[key]:
                    msg = '[config changed] '
                    config_changed = True
                    break
            else:
                msg = ''
            # this value is not covered by the above loop because it is handled
            # specially by the config class
            if self.config.extensions != config.extensions:
                msg = '[extensions changed] '
                config_changed = True
        # the source and doctree directories may have been relocated
        self.srcdir = srcdir
        self.doctreedir = doctreedir
        self.find_files(config)

        added, changed, removed = self.get_outdated_files(config_changed)

        # if files were added or removed, all documents with globbed toctrees
        # must be reread
        if added or removed:
            changed.update(self.glob_toctrees)

        msg += '%s added, %s changed, %s removed' % (len(added), len(changed),
                                                     len(removed))
        yield msg

        self.config = config
        self.app = app

        # clear all files no longer present
        for docname in removed:
            self.clear_doc(docname)

        # read all new and changed files
        for docname in sorted(added | changed):
            yield docname
            self.read_doc(docname, app=app)

        if config.master_doc not in self.all_docs:
            self.warn(None, 'master file %s not found' %
                      self.doc2path(config.master_doc))

        self.app = None

        # remove all non-existing images from inventory
        for imgsrc in self.images.keys():
            if not os.access(path.join(self.srcdir, imgsrc), os.R_OK):
                del self.images[imgsrc]

        if app:
            app.emit('env-updated', self)


    # --------- SINGLE FILE READING --------------------------------------------

    def read_doc(self, docname, src_path=None, save_parsed=True, app=None):
        """
        Parse a file and add/update inventory entries for the doctree.
        If srcpath is given, read from a different source file.
        """
        # remove all inventory entries for that file
        self.clear_doc(docname)

        if src_path is None:
            src_path = self.doc2path(docname)

        if self.config.default_role:
            role_fn, messages = roles.role(self.config.default_role, english,
                                           0, dummy_reporter)
            if role_fn:
                roles._roles[''] = role_fn
            else:
                self.warn(docname, 'default role %s not found' %
                          self.config.default_role)
        self.docname = docname
        doctree = publish_doctree(None, src_path, FileInput,
                                  settings_overrides=self.settings,
                                  reader=SphinxStandaloneReader())
        self.filter_messages(doctree)
        self.process_dependencies(docname, doctree)
        self.process_images(docname, doctree)
        self.process_metadata(docname, doctree)
        self.create_title_from(docname, doctree)
        self.note_labels_from(docname, doctree)
        self.note_indexentries_from(docname, doctree)
        self.build_toc_from(docname, doctree)

        # store time of reading, used to find outdated files
        self.all_docs[docname] = time.time()

        if app:
            app.emit('doctree-read', doctree)

        # make it picklable
        doctree.reporter = None
        doctree.transformer = None
        doctree.settings.warning_stream = None
        doctree.settings.env = None
        doctree.settings.record_dependencies = None

        # cleanup
        self.docname = None
        self.currmodule = None
        self.currclass = None
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

    def filter_messages(self, doctree):
        """
        Filter system messages from a doctree.
        """
        filterlevel = self.config.keep_warnings and 2 or 5
        for node in doctree.traverse(nodes.system_message):
            if node['level'] < filterlevel:
                node.parent.remove(node)

    def process_dependencies(self, docname, doctree):
        """
        Process docutils-generated dependency info.
        """
        deps = doctree.settings.record_dependencies
        if not deps:
            return
        docdir = path.dirname(self.doc2path(docname, base=None))
        for dep in deps.list:
            dep = path.join(docdir, dep)
            self.dependencies.setdefault(docname, set()).add(dep)

    def process_images(self, docname, doctree):
        """
        Process and rewrite image URIs.
        """
        existing_names = set(v[1] for v in self.images.itervalues())
        docdir = path.dirname(self.doc2path(docname, base=None))
        for node in doctree.traverse(nodes.image):
            # Map the mimetype to the corresponding image.  The writer may
            # choose the best image from these candidates.  The special key * is
            # set if there is only single candiate to be used by a writer.
            # The special key ? is set for nonlocal URIs.
            node['candidates'] = candidates = {}
            imguri = node['uri']
            if imguri.find('://') != -1:
                self.warn(docname, 'Nonlocal image URI found: %s' % imguri, node.line)
                candidates['?'] = imguri
                continue
            imgpath = path.normpath(path.join(docdir, imguri))
            node['uri'] = imgpath
            if imgpath.endswith(os.extsep + '*'):
                for filename in glob(path.join(self.srcdir, imgpath)):
                    dir, base = path.split(filename)
                    if base.lower().endswith('.pdf'):
                        candidates['application/pdf'] = path.join(docdir, base)
                    elif base.lower().endswith('.svg'):
                        candidates['image/svg+xml'] = path.join(docdir, base)
                    else:
                        f = open(filename, 'rb')
                        try:
                            imgtype = imghdr.what(f)
                        finally:
                            f.close()
                        if imgtype:
                            candidates['image/' + imgtype] = path.join(docdir, base)
            else:
                candidates['*'] = imgpath
            for imgpath in candidates.itervalues():
                self.dependencies.setdefault(docname, set()).add(imgpath)
                if not os.access(path.join(self.srcdir, imgpath), os.R_OK):
                    self.warn(docname, 'Image file not readable: %s' % imgpath,
                              node.line)
                if imgpath in self.images:
                    self.images[imgpath][0].add(docname)
                    continue
                uniquename = path.basename(imgpath)
                base, ext = path.splitext(uniquename)
                i = 0
                while uniquename in existing_names:
                    i += 1
                    uniquename = '%s%s%s' % (base, i, ext)
                self.images[imgpath] = (set([docname]), uniquename)
                existing_names.add(uniquename)

    def process_metadata(self, docname, doctree):
        """
        Process the docinfo part of the doctree as metadata.
        """
        self.metadata[docname] = md = {}
        try:
            docinfo = doctree[0]
        except IndexError:
            # probably an empty document
            return
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
            visitor = SphinxContentsFilter(document)
            node[0].walkabout(visitor)
            titlenode += visitor.get_entry_text()
            self.titles[docname] = titlenode
            return

    def note_labels_from(self, docname, document):
        for name, explicit in document.nametypes.iteritems():
            if not explicit:
                continue
            labelid = document.nameids[name]
            if labelid is None:
                continue
            node = document.ids[labelid]
            if name.isdigit() or node.has_key('refuri') or \
                   node.tagname.startswith('desc_'):
                # ignore footnote labels, labels automatically generated from a
                # link and description units
                continue
            if name in self.labels:
                self.warn(docname, 'duplicate label %s, ' % name +
                          'other instance in %s' % self.doc2path(self.labels[name][0]),
                          node.line)
            self.anonlabels[name] = docname, labelid
            if not isinstance(node, nodes.section):
                # anonymous-only labels
                continue
            sectname = node[0].astext() # node[0] == title node
            self.labels[name] = docname, labelid, sectname

    def note_indexentries_from(self, docname, document):
        entries = self.indexentries[docname] = []
        for node in document.traverse(addnodes.index):
            entries.extend(node['entries'])

    def note_toctree(self, docname, toctreenode):
        """Note a TOC tree directive in a document and gather information about
           file relations from it."""
        if toctreenode['glob']:
            self.glob_toctrees.add(docname)
        includefiles = toctreenode['includefiles']
        for includefile in includefiles:
            # note that if the included file is rebuilt, this one must be
            # too (since the TOC of the included file could have changed)
            self.files_to_rebuild.setdefault(includefile, set()).add(docname)
        self.toctree_includes.setdefault(docname, []).extend(includefiles)

    def build_toc_from(self, docname, document):
        """Build a TOC from the doctree and store it in the inventory."""
        numentries = [0] # nonlocal again...

        try:
            maxdepth = int(self.metadata[docname].get('tocdepth', 0))
        except ValueError:
            maxdepth = 0

        def build_toc(node, depth=1):
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
                visitor = SphinxContentsFilter(document)
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
                if maxdepth == 0 or depth < maxdepth:
                    item += build_toc(subnode, depth+1)
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
    def note_descref(self, fullname, desctype, line):
        if fullname in self.descrefs:
            self.warn(self.docname,
                      'duplicate canonical description name %s, ' % fullname +
                      'other instance in %s' % self.doc2path(self.descrefs[fullname][0]),
                      line)
        self.descrefs[fullname] = (self.docname, desctype)

    def note_module(self, modname, synopsis, platform, deprecated):
        self.modules[modname] = (self.docname, synopsis, platform, deprecated)
        self.filemodules.setdefault(self.docname, []).append(modname)

    def note_reftarget(self, type, name, labelid):
        self.reftargets[type, name] = (self.docname, labelid)

    def note_versionchange(self, type, version, node, lineno):
        self.versionchanges.setdefault(version, []).append(
            (type, self.docname, lineno, self.currmodule, self.currdesc, node.astext()))

    def note_dependency(self, filename):
        basename = path.dirname(self.doc2path(self.docname, base=None))
        # this will do the right thing when filename is absolute too
        filename = path.join(basename, filename)
        self.dependencies.setdefault(self.docname, set()).add(filename)
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
        doctree.settings.env = self
        doctree.reporter = Reporter(self.doc2path(docname), 2, 4,
                                    stream=RedirStream(self._warnfunc))
        return doctree


    def get_and_resolve_doctree(self, docname, builder, doctree=None,
                                prune_toctrees=True):
        """Read the doctree from the pickle, resolve cross-references and
           toctrees and return it."""
        if doctree is None:
            doctree = self.get_doctree(docname)

        # resolve all pending cross-references
        self.resolve_references(doctree, docname, builder)

        # now, resolve all toctree nodes
        for toctreenode in doctree.traverse(addnodes.toctree):
            result = self.resolve_toctree(docname, builder, toctreenode,
                                          prune=prune_toctrees)
            if result is None:
                toctreenode.replace_self([])
            else:
                toctreenode.replace_self(result)

        return doctree

    def resolve_toctree(self, docname, builder, toctree, prune=True, maxdepth=0,
                        titles_only=False):
        """
        Resolve a *toctree* node into individual bullet lists with titles
        as items, returning None (if no containing titles are found) or
        a new node.

        If *prune* is True, the tree is pruned to *maxdepth*, or if that is 0,
        to the value of the *maxdepth* option on the *toctree* node.
        If *titles_only* is True, only toplevel document titles will be in the
        resulting tree.
        """

        def _walk_depth(node, depth, maxdepth, titleoverrides):
            """Utility: Cut a TOC at a specified depth."""
            for subnode in node.children[:]:
                if isinstance(subnode, (addnodes.compact_paragraph, nodes.list_item)):
                    _walk_depth(subnode, depth, maxdepth, titleoverrides)
                elif isinstance(subnode, nodes.bullet_list):
                    if depth > maxdepth:
                        subnode.parent.replace(subnode, [])
                    else:
                        _walk_depth(subnode, depth+1, maxdepth, titleoverrides)

        def _entries_from_toctree(toctreenode, separate=False):
            """Return TOC entries for a toctree node."""
            includefiles = map(str, toctreenode['includefiles'])

            entries = []
            for includefile in includefiles:
                try:
                    toc = self.tocs[includefile].deepcopy()
                    if not toc.children:
                        # empty toc means: no titles will show up in the toctree
                        self.warn(docname, 'toctree contains reference to document '
                                  '%r that doesn\'t have a title: no link will be '
                                  'generated' % includefile)
                except KeyError:
                    # this is raised if the included file does not exist
                    self.warn(docname, 'toctree contains reference to nonexisting '
                              'document %r' % includefile)
                else:
                    # if titles_only is given, only keep the main title and
                    # sub-toctrees
                    if titles_only:
                        # delete everything but the toplevel title(s) and toctrees
                        for toplevel in toc:
                            # nodes with length 1 don't have any children anyway
                            if len(toplevel) > 1:
                                subtoctrees = toplevel.traverse(addnodes.toctree)
                                toplevel[1][:] = subtoctrees
                    # resolve all sub-toctrees
                    for toctreenode in toc.traverse(addnodes.toctree):
                        i = toctreenode.parent.index(toctreenode) + 1
                        for item in _entries_from_toctree(toctreenode):
                            toctreenode.parent.insert(i, item)
                            i += 1
                        toctreenode.parent.remove(toctreenode)
                    if separate:
                        entries.append(toc)
                    else:
                        entries.extend(toc.children)
            return entries

        maxdepth = maxdepth or toctree.get('maxdepth', -1)
        titleoverrides = toctree.get('includetitles', {})

        tocentries = _entries_from_toctree(toctree, separate=True)
        if not tocentries:
            return None

        newnode = addnodes.compact_paragraph('', '', *tocentries)
        newnode['toctree'] = True
        # prune the tree to maxdepth and replace titles
        if maxdepth > 0 and prune:
            _walk_depth(newnode, 1, maxdepth, titleoverrides)
        # replace titles, if needed, and set the target paths in the
        # toctrees (they are not known at TOC generation time)
        for refnode in newnode.traverse(nodes.reference):
            refnode['refuri'] = builder.get_relative_uri(
                docname, refnode['refuri']) + refnode['anchorname']
            if titleoverrides and not refnode['anchorname'] \
                   and refnode['refuri'] in titleoverrides:
                newtitle = titleoverrides[refnode['refuri']]
                refnode.children = [nodes.Text(newtitle)]
        return newnode

    descroles = frozenset(('data', 'exc', 'func', 'class', 'const', 'attr',
                           'meth', 'cfunc', 'cdata', 'ctype', 'cmacro', 'obj'))

    def resolve_references(self, doctree, fromdocname, builder):
        reftarget_roles = set(('token', 'term', 'option'))
        # add all custom xref types too
        reftarget_roles.update(i[0] for i in additional_xref_types.values())

        for node in doctree.traverse(addnodes.pending_xref):
            contnode = node[0].deepcopy()
            newnode = None

            typ = node['reftype']
            target = node['reftarget']

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
                        #self.warn(fromdocname, 'unknown keyword: %s' % target)
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
                            self.warn(fromdocname, 'term not in glossary: %s' % target,
                                      node.line)
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
                    if not docname:
                        newnode = builder.app.emit_firstresult('missing-reference',
                                                               self, node, contnode)
                        if not newnode:
                            newnode = contnode
                    elif docname == fromdocname:
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
                        newnode = builder.app.emit_firstresult('missing-reference',
                                                               self, node, contnode)
                        if not newnode:
                            newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if desc[0] == fromdocname:
                            newnode['refid'] = name
                        else:
                            newnode['refuri'] = (
                                builder.get_relative_uri(fromdocname, desc[0])
                                + '#' + name)
                        newnode['reftitle'] = name
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
                    except ValueError:
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
        return [(key, list(group)) for (key, group) in groupby(newlist, keyfunc)]

    def collect_relations(self):
        relations = {}
        getinc = self.toctree_includes.get
        def collect(parents, docname, previous, next):
            includes = getinc(docname)
            # previous
            if not previous:
                # if no previous sibling, go to parent
                previous = parents[0][0]
            else:
                # else, go to previous sibling, or if it has children, to
                # the last of its children, or if that has children, to the
                # last of those, and so forth
                while 1:
                    previncs = getinc(previous)
                    if previncs:
                        previous = previncs[-1]
                    else:
                        break
            # next
            if includes:
                # if it has children, go to first of them
                next = includes[0]
            elif next:
                # else, if next sibling, go to it
                pass
            else:
                # else, go to the next sibling of the parent, if present,
                # else the grandparent's sibling, if present, and so forth
                for parname, parindex in parents:
                    parincs = getinc(parname)
                    if parincs and parindex + 1 < len(parincs):
                        next = parincs[parindex+1]
                        break
                # else it will stay None
            # same for children
            if includes:
                for subindex, args in enumerate(izip(includes, [None] + includes,
                                                     includes[1:] + [None])):
                    collect([(docname, subindex)] + parents, *args)
            relations[docname] = [parents[0][0], previous, next]
        collect([(None, 0)], self.config.master_doc, None, None)
        return relations

    def check_consistency(self):
        """Do consistency checks."""

        for docname in sorted(self.all_docs):
            if docname not in self.files_to_rebuild:
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
