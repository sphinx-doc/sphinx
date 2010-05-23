# -*- coding: utf-8 -*-
"""
    sphinx.environment
    ~~~~~~~~~~~~~~~~~~

    Global creation environment.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import os
import time
import heapq
import types
import codecs
import imghdr
import string
import difflib
import cPickle as pickle
from os import path
from glob import glob
from itertools import izip, groupby

from docutils import nodes
from docutils.io import FileInput, NullOutput
from docutils.core import Publisher
from docutils.utils import Reporter, relative_path
from docutils.readers import standalone
from docutils.parsers.rst import roles
from docutils.parsers.rst.languages import en as english
from docutils.parsers.rst.directives.html import MetaBody
from docutils.writers import UnfilteredWriter
from docutils.transforms import Transform
from docutils.transforms.parts import ContentsFilter

from sphinx import addnodes
from sphinx.util import movefile, get_matching_docs, SEP, ustrftime, \
     docname_join, FilenameUniqDict, url_re, clean_astext
from sphinx.errors import SphinxError
from sphinx.directives import additional_xref_types

default_settings = {
    'embed_stylesheet': False,
    'cloak_email_addresses': True,
    'pep_base_url': 'http://www.python.org/dev/peps/',
    'rfc_base_url': 'http://tools.ietf.org/html/',
    'input_encoding': 'utf-8-sig',
    'doctitle_xform': False,
    'sectsubtitle_xform': False,
}

# This is increased every time an environment attribute is added
# or changed to properly invalidate pickle files.
ENV_VERSION = 31


default_substitutions = set([
    'version',
    'release',
    'today',
])

dummy_reporter = Reporter('', 4, 4)


class WarningStream(object):
    def __init__(self, warnfunc):
        self.warnfunc = warnfunc
    def write(self, text):
        if text.strip():
            self.warnfunc(text, None, '')


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
                    text = ustrftime(config.today_fmt or _('%B %d, %Y'))
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
                   node.parent.__class__ is nodes.section and \
                   node.has_key('ismod'):
                node.parent['ids'] = node['ids']
                node.parent.remove(node)


class HandleCodeBlocks(Transform):
    """
    Move doctest blocks out of blockquotes.
    """
    default_priority = 210

    def apply(self):
        for node in self.document.traverse(nodes.block_quote):
            if len(node.children) == 1 and isinstance(node.children[0],
                                                      nodes.doctest_block):
                node.replace_self(node.children[0])


class SortIds(Transform):
    """
    Sort secion IDs so that the "id[0-9]+" one comes last.
    """
    default_priority = 261

    def apply(self):
        for node in self.document.traverse(nodes.section):
            if len(node['ids']) > 1 and node['ids'][0].startswith('id'):
                node['ids'] = node['ids'][1:] + [node['ids'][0]]


class CitationReferences(Transform):
    """
    Handle citation references before the default docutils transform does.
    """
    default_priority = 619

    def apply(self):
        for citnode in self.document.traverse(nodes.citation_reference):
            cittext = citnode.astext()
            refnode = addnodes.pending_xref(cittext, reftype='citation',
                                            reftarget=cittext)
            refnode += nodes.Text('[' + cittext + ']')
            citnode.parent.replace(citnode, refnode)


class SphinxStandaloneReader(standalone.Reader):
    """
    Add our own transforms.
    """
    transforms = [CitationReferences, DefaultSubstitutions, MoveModuleTargets,
                  HandleCodeBlocks, SortIds]

    def get_transforms(self):
        return standalone.Reader.get_transforms(self) + self.transforms


class SphinxDummyWriter(UnfilteredWriter):
    supported = ('html',)  # needed to keep "meta" nodes

    def translate(self):
        pass


class SphinxContentsFilter(ContentsFilter):
    """
    Used with BuildEnvironment.add_toc_from() to discard cross-file links
    within table-of-contents link nodes.
    """
    def visit_pending_xref(self, node):
        text = node.astext()
        self.parent.append(nodes.literal(text, text))
        raise nodes.SkipNode

    def visit_image(self, node):
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
        # first write to a temporary file, so that if dumping fails,
        # the existing environment won't be overwritten
        picklefile = open(filename + '.tmp', 'wb')
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
        movefile(filename + '.tmp', filename)
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

        # All "docnames" here are /-separated and relative and exclude
        # the source suffix.

        self.found_docs = set()     # contains all existing docnames
        self.all_docs = {}          # docname -> mtime at the time of build
                                    # contains all built docnames
        self.dependencies = {}      # docname -> set of dependent file
                                    # names, relative to documentation root

        # File metadata
        self.metadata = {}          # docname -> dict of metadata items

        # TOC inventory
        self.titles = {}            # docname -> title node
        self.longtitles = {}        # docname -> title node; only different if
                                    # set differently with title directive
        self.tocs = {}              # docname -> table of contents nodetree
        self.toc_num_entries = {}   # docname -> number of real entries
        # used to determine when to show the TOC
        # in a sidebar (don't show if it's only one item)
        self.toc_secnumbers = {}    # docname -> dict of sectionid -> number

        self.toctree_includes = {}  # docname -> list of toctree includefiles
        self.files_to_rebuild = {}  # docname -> set of files
                                    # (containing its TOCs) to rebuild too
        self.glob_toctrees = set()  # docnames that have :glob: toctrees
        self.numbered_toctrees = set() # docnames that have :numbered: toctrees

        # X-ref target inventory
        self.descrefs = {}          # fullname -> docname, desctype
        self.filemodules = {}       # docname -> [modules]
        self.modules = {}           # modname -> docname, synopsis,
                                    #            platform, deprecated
        self.labels = {}            # labelname -> docname, labelid, sectionname
        self.anonlabels = {}        # labelname -> docname, labelid
        self.progoptions = {}       # (program, name) -> docname, labelid
        self.reftargets = {}        # (type, name) -> docname, labelid
                                    # type: term, token, envvar, citation

        # Other inventories
        self.indexentries = {}      # docname -> list of
                                    # (type, string, target, aliasname)
        self.versionchanges = {}    # version -> list of (type, docname,
                                    # lineno, module, descname, content)

        # these map absolute path -> (docnames, unique filename)
        self.images = FilenameUniqDict()
        self.dlfiles = FilenameUniqDict()

        # These are set while parsing a file
        self.docname = None         # current document name
        self.currmodule = None      # current module name
        self.currclass = None       # current class name
        self.currdesc = None        # current descref name
        self.currprogram = None     # current program name
        self.index_num = 0          # autonumber for index targets
        self.gloss_entries = set()  # existing definition labels

        # Some magically present labels
        def add_magic_label(name, description):
            self.labels[name] = (name, '', description)
            self.anonlabels[name] = (name, '')
        add_magic_label('genindex', _('Index'))
        add_magic_label('modindex', _('Module Index'))
        add_magic_label('search', _('Search Page'))

    def set_warnfunc(self, func):
        self._warnfunc = func
        self.settings['warning_stream'] = WarningStream(func)

    def warn(self, docname, msg, lineno=None):
        if docname:
            if lineno is None:
                lineno = ''
            self._warnfunc(msg, '%s:%s' % (self.doc2path(docname), lineno))
        else:
            self._warnfunc(msg)

    def clear_doc(self, docname):
        """Remove all traces of a source file in the inventory."""
        if docname in self.all_docs:
            self.all_docs.pop(docname, None)
            self.metadata.pop(docname, None)
            self.dependencies.pop(docname, None)
            self.titles.pop(docname, None)
            self.longtitles.pop(docname, None)
            self.tocs.pop(docname, None)
            self.toc_secnumbers.pop(docname, None)
            self.toc_num_entries.pop(docname, None)
            self.toctree_includes.pop(docname, None)
            self.filemodules.pop(docname, None)
            self.indexentries.pop(docname, None)
            self.glob_toctrees.discard(docname)
            self.numbered_toctrees.discard(docname)
            self.images.purge_doc(docname)
            self.dlfiles.purge_doc(docname)

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
            for key, (fn, _) in self.progoptions.items():
                if fn == docname:
                    del self.progoptions[key]
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
            return path.join(self.srcdir,
                             docname.replace(SEP, path.sep)) + suffix
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
            self.srcdir, config.source_suffix,
            exclude_docs=set(config.unused_docs),
            exclude_dirs=exclude_dirs,
            exclude_trees=exclude_trees,
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
        """
        (Re-)read all files new or changed since last update.  Returns a
        summary, the total count of documents to reread and an iterator that
        yields docnames as it processes them.  Store all environment docnames in
        the canonical format (ie using SEP as a separator in place of
        os.path.sep).
        """
        config_changed = False
        if self.config is None:
            msg = '[new config] '
            config_changed = True
        else:
            # check if a config value was changed that affects how
            # doctrees are read
            for key, descr in config.values.iteritems():
                if descr[1] != 'env':
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
        self.config = config

        added, changed, removed = self.get_outdated_files(config_changed)

        # if files were added or removed, all documents with globbed toctrees
        # must be reread
        if added or removed:
            changed.update(self.glob_toctrees)

        msg += '%s added, %s changed, %s removed' % (len(added), len(changed),
                                                     len(removed))

        def update_generator():
            self.app = app

            # clear all files no longer present
            for docname in removed:
                if app:
                    app.emit('env-purge-doc', self, docname)
                self.clear_doc(docname)

            # read all new and changed files
            to_read = added | changed
            for docname in sorted(to_read):
                yield docname
                self.read_doc(docname, app=app)

            if config.master_doc not in self.all_docs:
                self.warn(None, 'master file %s not found' %
                          self.doc2path(config.master_doc))

            self.app = None
            if app:
                app.emit('env-updated', self)

        return msg, len(added | changed), update_generator()

    def check_dependents(self, already):
        to_rewrite = self.assign_section_numbers()
        for docname in to_rewrite:
            if docname not in already:
                yield docname

    # --------- SINGLE FILE READING --------------------------------------------

    def warn_and_replace(self, error):
        """
        Custom decoding error handler that warns and replaces.
        """
        linestart = error.object.rfind('\n', 0, error.start)
        lineend = error.object.find('\n', error.start)
        if lineend == -1: lineend = len(error.object)
        lineno = error.object.count('\n', 0, error.start) + 1
        self.warn(self.docname, 'undecodable source characters, '
                  'replacing with "?": %r' %
                  (error.object[linestart+1:error.start] + '>>>' +
                   error.object[error.start:error.end] + '<<<' +
                   error.object[error.end:lineend]), lineno)
        return (u'?', error.end)

    def read_doc(self, docname, src_path=None, save_parsed=True, app=None):
        """
        Parse a file and add/update inventory entries for the doctree.
        If srcpath is given, read from a different source file.
        """
        # remove all inventory entries for that file
        if app:
            app.emit('env-purge-doc', self, docname)
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
        self.settings['input_encoding'] = self.config.source_encoding
        self.settings['trim_footnote_reference_space'] = \
            self.config.trim_footnote_reference_space

        codecs.register_error('sphinx', self.warn_and_replace)

        codecs.register_error('sphinx', self.warn_and_replace)

        class SphinxSourceClass(FileInput):
            def decode(self_, data):
                return data.decode(self_.encoding, 'sphinx')

            def read(self_):
                data = FileInput.read(self_)
                if app:
                    arg = [data]
                    app.emit('source-read', docname, arg)
                    data = arg[0]
                if self.config.rst_epilog:
                    return data + '\n' + self.config.rst_epilog + '\n'
                else:
                    return data

        # publish manually
        pub = Publisher(reader=SphinxStandaloneReader(),
                        writer=SphinxDummyWriter(),
                        source_class=SphinxSourceClass,
                        destination_class=NullOutput)
        pub.set_components(None, 'restructuredtext', None)
        pub.process_programmatic_settings(None, self.settings, None)
        pub.set_source(None, src_path)
        pub.set_destination(None, None)
        try:
            pub.publish()
            doctree = pub.document
        except UnicodeError, err:
            raise SphinxError(str(err))
        self.filter_messages(doctree)
        self.process_dependencies(docname, doctree)
        self.process_images(docname, doctree)
        self.process_downloads(docname, doctree)
        self.process_metadata(docname, doctree)
        self.create_title_from(docname, doctree)
        self.note_labels_from(docname, doctree)
        self.note_indexentries_from(docname, doctree)
        self.note_citations_from(docname, doctree)
        self.build_toc_from(docname, doctree)

        # store time of build, for outdated files detection
        self.all_docs[docname] = time.time()

        if app:
            app.emit('doctree-read', doctree)

        # make it picklable
        doctree.reporter = None
        doctree.transformer = None
        doctree.settings.warning_stream = None
        doctree.settings.env = None
        doctree.settings.record_dependencies = None
        for metanode in doctree.traverse(MetaBody.meta):
            # docutils' meta nodes aren't picklable because the class is nested
            metanode.__class__ = addnodes.meta

        # cleanup
        self.docname = None
        self.currmodule = None
        self.currclass = None
        self.gloss_entries = set()

        if save_parsed:
            # save the parsed doctree
            doctree_filename = self.doc2path(docname, self.doctreedir,
                                             '.doctree')
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
        cwd = os.getcwd()
        frompath = path.join(path.normpath(self.srcdir), 'dummy')
        deps = doctree.settings.record_dependencies
        if not deps:
            return
        for dep in deps.list:
            # the dependency path is relative to the working dir, so get
            # one relative to the srcdir
            relpath = relative_path(frompath,
                                    path.normpath(path.join(cwd, dep)))
            self.dependencies.setdefault(docname, set()).add(relpath)

    def process_downloads(self, docname, doctree):
        """
        Process downloadable file paths.
        """
        docdir = path.dirname(self.doc2path(docname, base=None))
        for node in doctree.traverse(addnodes.download_reference):
            targetname = node['reftarget']
            if targetname.startswith('/') or targetname.startswith(os.sep):
                # absolute
                filepath = targetname[1:]
            else:
                filepath = path.normpath(path.join(docdir, node['reftarget']))
            self.dependencies.setdefault(docname, set()).add(filepath)
            if not os.access(path.join(self.srcdir, filepath), os.R_OK):
                self.warn(docname, 'download file not readable: %s' % filepath,
                          getattr(node, 'line', None))
                continue
            uniquename = self.dlfiles.add_file(docname, filepath)
            node['filename'] = uniquename

    def process_images(self, docname, doctree):
        """
        Process and rewrite image URIs.
        """
        docdir = path.dirname(self.doc2path(docname, base=None))
        for node in doctree.traverse(nodes.image):
            # Map the mimetype to the corresponding image.  The writer may
            # choose the best image from these candidates.  The special key * is
            # set if there is only single candidate to be used by a writer.
            # The special key ? is set for nonlocal URIs.
            node['candidates'] = candidates = {}
            imguri = node['uri']
            if imguri.find('://') != -1:
                self.warn(docname, 'nonlocal image URI found: %s' % imguri,
                          node.line)
                candidates['?'] = imguri
                continue
            # imgpath is the image path *from srcdir*
            if imguri.startswith('/') or imguri.startswith(os.sep):
                # absolute path (= relative to srcdir)
                imgpath = path.normpath(imguri[1:])
            else:
                imgpath = path.normpath(path.join(docdir, imguri))
            # set imgpath as default URI
            node['uri'] = imgpath
            if imgpath.endswith(os.extsep + '*'):
                for filename in glob(path.join(self.srcdir, imgpath)):
                    new_imgpath = relative_path(self.srcdir, filename)
                    if filename.lower().endswith('.pdf'):
                        candidates['application/pdf'] = new_imgpath
                    elif filename.lower().endswith('.svg'):
                        candidates['image/svg+xml'] = new_imgpath
                    else:
                        try:
                            f = open(filename, 'rb')
                            try:
                                imgtype = imghdr.what(f)
                            finally:
                                f.close()
                        except (OSError, IOError):
                            self.warn(docname,
                                      'image file %s not readable' % filename)
                        if imgtype:
                            candidates['image/' + imgtype] = new_imgpath
            else:
                candidates['*'] = imgpath
            # map image paths to unique image names (so that they can be put
            # into a single directory)
            for imgpath in candidates.itervalues():
                self.dependencies.setdefault(docname, set()).add(imgpath)
                if not os.access(path.join(self.srcdir, imgpath), os.R_OK):
                    self.warn(docname, 'image file not readable: %s' % imgpath,
                              node.line)
                    continue
                self.images.add_file(docname, imgpath)

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
        titlenode = nodes.title()
        longtitlenode = titlenode
        # explicit title set with title directive; use this only for
        # the <title> tag in HTML output
        if document.has_key('title'):
            longtitlenode = nodes.title()
            longtitlenode += nodes.Text(document['title'])
        # look for first section title and use that as the title
        for node in document.traverse(nodes.section):
            visitor = SphinxContentsFilter(document)
            node[0].walkabout(visitor)
            titlenode += visitor.get_entry_text()
            break
        else:
            # document has no title
            titlenode += nodes.Text('<no title>')
        self.titles[docname] = titlenode
        self.longtitles[docname] = longtitlenode

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
                          'other instance in ' +
                          self.doc2path(self.labels[name][0]),
                          node.line)
            self.anonlabels[name] = docname, labelid
            if node.tagname == 'section':
                sectname = clean_astext(node[0]) # node[0] == title node
            elif node.tagname == 'figure':
                for n in node:
                    if n.tagname == 'caption':
                        sectname = clean_astext(n)
                        break
                else:
                    continue
            else:
                # anonymous-only labels
                continue
            self.labels[name] = docname, labelid, sectname

    def note_indexentries_from(self, docname, document):
        entries = self.indexentries[docname] = []
        for node in document.traverse(addnodes.index):
            entries.extend(node['entries'])

    def note_citations_from(self, docname, document):
        for node in document.traverse(nodes.citation):
            label = node[0].astext()
            if ('citation', label) in self.reftargets:
                self.warn(docname, 'duplicate citation %s, ' % label +
                          'other instance in %s' % self.doc2path(
                    self.reftargets['citation', label][0]), node.line)
            self.reftargets['citation', label] = (docname, node['ids'][0])

    def note_toctree(self, docname, toctreenode):
        """Note a TOC tree directive in a document and gather information about
           file relations from it."""
        if toctreenode['glob']:
            self.glob_toctrees.add(docname)
        if toctreenode.get('numbered'):
            self.numbered_toctrees.add(docname)
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

        def traverse_in_section(node, cls):
            """Like traverse(), but stay within the same section."""
            result = []
            if isinstance(node, cls):
                result.append(node)
            for child in node.children:
                if isinstance(child, nodes.section):
                    continue
                result.extend(traverse_in_section(child, cls))
            return result

        def build_toc(node, depth=1):
            entries = []
            for sectionnode in node:
                # find all toctree nodes in this section and add them
                # to the toc (just copying the toctree node which is then
                # resolved in self.get_and_resolve_doctree)
                if not isinstance(sectionnode, nodes.section):
                    for toctreenode in traverse_in_section(sectionnode,
                                                           addnodes.toctree):
                        item = toctreenode.copy()
                        entries.append(item)
                        # important: do the inventory stuff
                        self.note_toctree(docname, toctreenode)
                    continue
                title = sectionnode[0]
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
                    anchorname = '#' + sectionnode['ids'][0]
                numentries[0] += 1
                reference = nodes.reference('', '', refuri=docname,
                                            anchorname=anchorname,
                                            *nodetext)
                para = addnodes.compact_paragraph('', '', reference)
                item = nodes.list_item('', para)
                if maxdepth == 0 or depth < maxdepth:
                    item += build_toc(sectionnode, depth+1)
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
            node['refuri'] = node['anchorname'] or '#'
        return toc

    def get_toctree_for(self, docname, builder, collapse):
        """Return the global TOC nodetree."""
        doctree = self.get_doctree(self.config.master_doc)
        toctrees = []
        for toctreenode in doctree.traverse(addnodes.toctree):
            toctree = self.resolve_toctree(docname, builder, toctreenode,
                                           prune=True, collapse=collapse,
                                           includehidden=True)
            toctrees.append(toctree)
        if not toctrees:
            return None
        result = toctrees[0]
        for toctree in toctrees[1:]:
            result.extend(toctree.children)
        return result

    # -------
    # these are called from docutils directives and therefore use self.docname
    #
    def note_descref(self, fullname, desctype, line):
        if fullname in self.descrefs:
            self.warn(self.docname,
                      'duplicate canonical description name %s, ' % fullname +
                      'other instance in ' +
                      self.doc2path(self.descrefs[fullname][0]) +
                      ', use :noindex: for one of them',
                      line)
        self.descrefs[fullname] = (self.docname, desctype)

    def note_module(self, modname, synopsis, platform, deprecated):
        self.modules[modname] = (self.docname, synopsis, platform, deprecated)
        self.filemodules.setdefault(self.docname, []).append(modname)

    def note_progoption(self, optname, labelid):
        self.progoptions[self.currprogram, optname] = (self.docname, labelid)

    def note_reftarget(self, type, name, labelid):
        self.reftargets[type, name] = (self.docname, labelid)

    def note_versionchange(self, type, version, node, lineno):
        self.versionchanges.setdefault(version, []).append(
            (type, self.docname, lineno, self.currmodule, self.currdesc,
             node.astext()))

    def note_dependency(self, filename):
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
                                    stream=WarningStream(self._warnfunc))
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
                        titles_only=False, collapse=False, includehidden=False):
        """
        Resolve a *toctree* node into individual bullet lists with titles
        as items, returning None (if no containing titles are found) or
        a new node.

        If *prune* is True, the tree is pruned to *maxdepth*, or if that is 0,
        to the value of the *maxdepth* option on the *toctree* node.
        If *titles_only* is True, only toplevel document titles will be in the
        resulting tree.
        If *collapse* is True, all branches not containing docname will
        be collapsed.
        """
        if toctree.get('hidden', False) and not includehidden:
            return None

        def _walk_depth(node, depth, maxdepth):
            """Utility: Cut a TOC at a specified depth."""
            for subnode in node.children[:]:
                if isinstance(subnode, (addnodes.compact_paragraph,
                                        nodes.list_item)):
                    subnode['classes'].append('toctree-l%d' % (depth-1))
                    _walk_depth(subnode, depth, maxdepth)
                elif isinstance(subnode, nodes.bullet_list):
                    if maxdepth > 0 and depth > maxdepth:
                        subnode.parent.replace(subnode, [])
                    else:
                        _walk_depth(subnode, depth+1, maxdepth)

                        # cull sub-entries whose parents aren't 'current'
                        if (collapse and
                            depth > 1 and
                            'current' not in subnode.parent['classes']):
                            subnode.parent.remove(subnode)

                elif isinstance(subnode, nodes.reference):
                    # identify the toc entry pointing to the current document
                    if subnode['refuri'] == docname and \
                           not subnode['anchorname']:
                        # tag the whole branch as 'current'
                        p = subnode
                        while p:
                            p['classes'].append('current')
                            p = p.parent

        def _entries_from_toctree(toctreenode, separate=False, subtree=False):
            """Return TOC entries for a toctree node."""
            refs = [(e[0], str(e[1])) for e in toctreenode['entries']]
            entries = []
            for (title, ref) in refs:
                try:
                    if url_re.match(ref):
                        reference = nodes.reference('', '',
                                                    refuri=ref, anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        toc = nodes.bullet_list('', item)
                    elif ref == 'self':
                        # 'self' refers to the document from which this
                        # toctree originates
                        ref = toctreenode['parent']
                        if not title:
                            title = clean_astext(self.titles[ref])
                        reference = nodes.reference('', '',
                                                    refuri=ref,
                                                    anchorname='',
                                                    *[nodes.Text(title)])
                        para = addnodes.compact_paragraph('', '', reference)
                        item = nodes.list_item('', para)
                        # don't show subitems
                        toc = nodes.bullet_list('', item)
                    else:
                        toc = self.tocs[ref].deepcopy()
                        if title and toc.children and len(toc.children) == 1:
                            child = toc.children[0]
                            for refnode in child.traverse(nodes.reference):
                                if refnode['refuri'] == ref and \
                                       not refnode['anchorname']:
                                    refnode.children = [nodes.Text(title)]
                    if not toc.children:
                        # empty toc means: no titles will show up in the toctree
                        self.warn(docname,
                                  'toctree contains reference to document '
                                  '%r that doesn\'t have a title: no link '
                                  'will be generated' % ref)
                except KeyError:
                    # this is raised if the included file does not exist
                    self.warn(docname, 'toctree contains reference to '
                              'nonexisting document %r' % ref)
                else:
                    # if titles_only is given, only keep the main title and
                    # sub-toctrees
                    if titles_only:
                        # delete everything but the toplevel title(s)
                        # and toctrees
                        for toplevel in toc:
                            # nodes with length 1 don't have any children anyway
                            if len(toplevel) > 1:
                                subtrees = toplevel.traverse(addnodes.toctree)
                                toplevel[1][:] = subtrees
                    # resolve all sub-toctrees
                    for toctreenode in toc.traverse(addnodes.toctree):
                        i = toctreenode.parent.index(toctreenode) + 1
                        for item in _entries_from_toctree(toctreenode,
                                                          subtree=True):
                            toctreenode.parent.insert(i, item)
                            i += 1
                        toctreenode.parent.remove(toctreenode)
                    if separate:
                        entries.append(toc)
                    else:
                        entries.extend(toc.children)
            if not subtree and not separate:
                ret = nodes.bullet_list()
                ret += entries
                return [ret]
            return entries

        maxdepth = maxdepth or toctree.get('maxdepth', -1)

        # NOTE: previously, this was separate=True, but that leads to artificial
        # separation when two or more toctree entries form a logical unit, so
        # separating mode is no longer used -- it's kept here for history's sake
        tocentries = _entries_from_toctree(toctree, separate=False)
        if not tocentries:
            return None

        newnode = addnodes.compact_paragraph('', '', *tocentries)
        newnode['toctree'] = True

        # prune the tree to maxdepth and replace titles, also set level classes
        _walk_depth(newnode, 1, prune and maxdepth or 0)

        # set the target paths in the toctrees (they are not known at TOC
        # generation time)
        for refnode in newnode.traverse(nodes.reference):
            if not url_re.match(refnode['refuri']):
                refnode['refuri'] = builder.get_relative_uri(
                    docname, refnode['refuri']) + refnode['anchorname']
        return newnode

    descroles = frozenset(('data', 'exc', 'func', 'class', 'const',
                           'attr', 'obj', 'meth', 'cfunc', 'cmember',
                           'cdata', 'ctype', 'cmacro'))

    def resolve_references(self, doctree, fromdocname, builder):
        reftarget_roles = set(('token', 'term', 'citation'))
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
                        # reference to anonymous label; the reference uses
                        # the supplied link caption
                        docname, labelid = self.anonlabels.get(target, ('',''))
                        sectname = node.astext()
                        if not docname:
                            self.warn(node['refdoc'], 'undefined label: %s' %
                                      target, node.line)
                    else:
                        # reference to the named label; the final node will
                        # contain the section name after the label
                        docname, labelid, sectname = self.labels.get(target,
                                                                     ('','',''))
                        if not docname:
                            self.warn(
                                node['refdoc'],
                                'undefined label: %s' % target + ' -- if you '
                                'don\'t give a link caption the label must '
                                'precede a section header.', node.line)
                    if docname:
                        newnode = nodes.reference('', '')
                        innernode = nodes.emphasis(sectname, sectname)
                        if docname == fromdocname:
                            newnode['refid'] = labelid
                        else:
                            # set more info in contnode; in case the
                            # get_relative_uri call raises NoUri,
                            # the builder will then have to resolve these
                            contnode = addnodes.pending_xref('')
                            contnode['refdocname'] = docname
                            contnode['refsectname'] = sectname
                            newnode['refuri'] = builder.get_relative_uri(
                                fromdocname, docname)
                            if labelid:
                                newnode['refuri'] += '#' + labelid
                        newnode.append(innernode)
                    else:
                        newnode = contnode
                elif typ == 'doc':
                    # directly reference to document by source name;
                    # can be absolute or relative
                    docname = docname_join(node['refdoc'], target)
                    if docname not in self.all_docs:
                        self.warn(node['refdoc'],
                                  'unknown document: %s' % docname, node.line)
                        newnode = contnode
                    else:
                        if node['refcaption']:
                            # reference with explicit title
                            caption = node.astext()
                        else:
                            caption = clean_astext(self.titles[docname])
                        innernode = nodes.emphasis(caption, caption)
                        newnode = nodes.reference('', '')
                        newnode['refuri'] = builder.get_relative_uri(
                            fromdocname, docname)
                        newnode.append(innernode)
                elif typ == 'keyword':
                    # keywords are referenced by named labels
                    docname, labelid, _ = self.labels.get(target, ('','',''))
                    if not docname:
                        #self.warn(node['refdoc'],
                        #          'unknown keyword: %s' % target)
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        if docname == fromdocname:
                            newnode['refid'] = labelid
                        else:
                            newnode['refuri'] = builder.get_relative_uri(
                                fromdocname, docname) + '#' + labelid
                        newnode.append(contnode)
                elif typ == 'option':
                    progname = node['refprogram']
                    docname, labelid = self.progoptions.get((progname, target),
                                                            ('', ''))
                    if not docname:
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
                    docname, labelid = self.reftargets.get((typ, target),
                                                           ('', ''))
                    if not docname:
                        if typ == 'term':
                            self.warn(node['refdoc'],
                                      'term not in glossary: %s' % target,
                                      node.line)
                        elif typ == 'citation':
                            self.warn(node['refdoc'],
                                      'citation not found: %s' % target,
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
                elif typ == 'mod' or \
                         typ == 'obj' and target in self.modules:
                    docname, synopsis, platform, deprecated = \
                        self.modules.get(target, ('','','', ''))
                    if not docname:
                        newnode = builder.app.emit_firstresult(
                            'missing-reference', self, node, contnode)
                        if not newnode:
                            newnode = contnode
                    elif docname == fromdocname:
                        # don't link to self
                        newnode = contnode
                    else:
                        newnode = nodes.reference('', '')
                        newnode['refuri'] = builder.get_relative_uri(
                            fromdocname, docname) + '#module-' + target
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
                        newnode = builder.app.emit_firstresult(
                            'missing-reference', self, node, contnode)
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
                    raise RuntimeError('unknown xfileref node encountered: %s'
                                       % node)
            except NoUri:
                newnode = contnode
            if newnode:
                node.replace_self(newnode)

        for node in doctree.traverse(addnodes.only):
            try:
                ret = builder.tags.eval_condition(node['expr'])
            except Exception, err:
                self.warn(fromdocname, 'exception while evaluating only '
                          'directive expression: %s' % err, node.line)
                node.replace_self(node.children)
            else:
                if ret:
                    node.replace_self(node.children)
                else:
                    node.replace_self([])

        # allow custom references to be resolved
        builder.app.emit('doctree-resolved', doctree, fromdocname)

    def assign_section_numbers(self):
        """Assign a section number to each heading under a numbered toctree."""
        # a list of all docnames whose section numbers changed
        rewrite_needed = []

        old_secnumbers = self.toc_secnumbers
        self.toc_secnumbers = {}

        def _walk_toc(node, secnums, titlenode=None):
            # titlenode is the title of the document, it will get assigned a
            # secnumber too, so that it shows up in next/prev/parent rellinks
            for subnode in node.children:
                if isinstance(subnode, nodes.bullet_list):
                    numstack.append(0)
                    _walk_toc(subnode, secnums, titlenode)
                    numstack.pop()
                    titlenode = None
                elif isinstance(subnode, nodes.list_item):
                    _walk_toc(subnode, secnums, titlenode)
                    titlenode = None
                elif isinstance(subnode, addnodes.compact_paragraph):
                    numstack[-1] += 1
                    secnums[subnode[0]['anchorname']] = \
                        subnode[0]['secnumber'] = tuple(numstack)
                    if titlenode:
                        titlenode['secnumber'] = tuple(numstack)
                        titlenode = None
                elif isinstance(subnode, addnodes.toctree):
                    _walk_toctree(subnode)

        def _walk_toctree(toctreenode):
            for (title, ref) in toctreenode['entries']:
                if url_re.match(ref) or ref == 'self':
                    # don't mess with those
                    continue
                if ref in self.tocs:
                    secnums = self.toc_secnumbers[ref] = {}
                    _walk_toc(self.tocs[ref], secnums, self.titles.get(ref))
                    if secnums != old_secnumbers.get(ref):
                        rewrite_needed.append(ref)

        for docname in self.numbered_toctrees:
            doctree = self.get_doctree(docname)
            for toctreenode in doctree.traverse(addnodes.toctree):
                if toctreenode.get('numbered'):
                    # every numbered toctree gets new numbering
                    numstack = [0]
                    _walk_toctree(toctreenode)

        return rewrite_needed

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
            # new entry types must be listed in directives/other.py!
            for type, value, tid, alias in entries:
                if type == 'single':
                    try:
                        entry, subentry = value.split(';', 1)
                    except ValueError:
                        entry, subentry = value, ''
                    if not entry:
                        self.warn(fn, 'invalid index entry %r' % value)
                        continue
                    add_entry(entry.strip(), subentry.strip())
                elif type == 'pair':
                    try:
                        first, second = map(lambda x: x.strip(),
                                            value.split(';', 1))
                        if not first or not second:
                            raise ValueError
                    except ValueError:
                        self.warn(fn, 'invalid pair index entry %r' % value)
                        continue
                    add_entry(first, second)
                    add_entry(second, first)
                elif type == 'triple':
                    try:
                        first, second, third = map(lambda x: x.strip(),
                                                   value.split(';', 2))
                        if not first or not second or not third:
                            raise ValueError
                    except ValueError:
                        self.warn(fn, 'invalid triple index entry %r' % value)
                        continue
                    add_entry(first, second+' '+third)
                    add_entry(second, third+', '+first)
                    add_entry(third, first+' '+second)
                else:
                    self.warn(fn, 'unknown index entry type %r' % type)

        # sort the index entries; put all symbols at the front, even those
        # following the letters in ASCII, this is where the chr(127) comes from
        def keyfunc(entry, lcletters=string.ascii_lowercase + '_'):
            lckey = entry[0].lower()
            if lckey[0:1] in lcletters:
                return chr(127) + lckey
            return lckey
        newlist = new.items()
        newlist.sort(key=keyfunc)

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
            # cannot move if it has subitems; structure gets too complex
            if not subitems:
                m = _fixre.match(key)
                if m:
                    if oldkey == m.group(1):
                        # prefixes match: add entry as subitem of the
                        # previous entry
                        oldsubitems.setdefault(m.group(2), [[], {}])[0].\
                                    extend(targets)
                        del newlist[i]
                        continue
                    oldkey = m.group(1)
                else:
                    oldkey = key
            oldsubitems = subitems
            i += 1

        # group the entries by letter
        def keyfunc((k, v), letters=string.ascii_uppercase + '_'):
            # hack: mutating the subitems dicts to a list in the keyfunc
            v[1] = sorted((si, se) for (si, (se, void)) in v[1].iteritems())
            # now calculate the key
            letter = k[0].upper()
            if letter in letters:
                return letter
            else:
                # get all other symbols under one heading
                return 'Symbols'
        return [(key, list(group))
                for (key, group) in groupby(newlist, keyfunc)]

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
                for subindex, args in enumerate(izip(includes,
                                                     [None] + includes,
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
            elif classname and classname + '.' + name in self.descrefs:
                newname = classname + '.' + name
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
        Find keyword matches for a keyword. If there's an exact match,
        just return it, else return a list of fuzzy matches if avoid_fuzzy
        isn't True.

        Keywords searched are: first modules, then descrefs.

        Returns: None if nothing found
                 (type, docname, anchorname) if exact match found
                 list of (quality, type, docname, anchorname, description)
                 if fuzzy
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
