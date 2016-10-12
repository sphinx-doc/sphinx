# -*- coding: utf-8 -*-
"""
    sphinx.environment
    ~~~~~~~~~~~~~~~~~~

    Global creation environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import os
import sys
import time
import types
import codecs
import fnmatch
from os import path
from glob import glob

from six import iteritems, itervalues, class_types, next
from six.moves import cPickle as pickle
from docutils import nodes
from docutils.io import NullOutput
from docutils.core import Publisher
from docutils.utils import Reporter, relative_path, get_source_line
from docutils.parsers.rst import roles
from docutils.parsers.rst.languages import en as english
from docutils.frontend import OptionParser

from sphinx import addnodes
from sphinx.io import SphinxStandaloneReader, SphinxDummyWriter, SphinxFileInput
from sphinx.util import get_matching_docs, docname_join, FilenameUniqDict
from sphinx.util.nodes import clean_astext, WarningStream, is_translatable, \
    process_only_nodes
from sphinx.util.osutil import SEP, getcwd, fs_encoding, ensuredir
from sphinx.util.images import guess_mimetype
from sphinx.util.i18n import find_catalog_files, get_image_filename_for_language, \
    search_image_for_language
from sphinx.util.console import bold, purple
from sphinx.util.docutils import sphinx_domains
from sphinx.util.matching import compile_matchers
from sphinx.util.parallel import ParallelTasks, parallel_available, make_chunks
from sphinx.util.websupport import is_commentable
from sphinx.errors import SphinxError, ExtensionError
from sphinx.versioning import add_uids, merge_doctrees
from sphinx.transforms import SphinxContentsFilter
from sphinx.environment.managers.indexentries import IndexEntries
from sphinx.environment.managers.toctree import Toctree


default_settings = {
    'embed_stylesheet': False,
    'cloak_email_addresses': True,
    'pep_base_url': 'https://www.python.org/dev/peps/',
    'rfc_base_url': 'https://tools.ietf.org/html/',
    'input_encoding': 'utf-8-sig',
    'doctitle_xform': False,
    'sectsubtitle_xform': False,
    'halt_level': 5,
    'file_insertion_enabled': True,
}

# This is increased every time an environment attribute is added
# or changed to properly invalidate pickle files.
#
# NOTE: increase base version by 2 to have distinct numbers for Py2 and 3
ENV_VERSION = 50 + (sys.version_info[0] - 2)


dummy_reporter = Reporter('', 4, 4)

versioning_conditions = {
    'none': False,
    'text': is_translatable,
    'commentable': is_commentable,
}


class NoUri(Exception):
    """Raised by get_relative_uri if there is no URI available."""
    pass


class BuildEnvironment(object):
    """
    The environment in which the ReST files are translated.
    Stores an inventory of cross-file targets and provides doctree
    transformations to resolve links to them.
    """

    # --------- ENVIRONMENT PERSISTENCE ----------------------------------------

    @staticmethod
    def frompickle(srcdir, config, filename):
        with open(filename, 'rb') as picklefile:
            env = pickle.load(picklefile)
        if env.version != ENV_VERSION:
            raise IOError('build environment version not current')
        if env.srcdir != srcdir:
            raise IOError('source directory has changed')
        env.config.values = config.values
        return env

    def topickle(self, filename):
        # remove unpicklable attributes
        warnfunc = self._warnfunc
        self.set_warnfunc(None)
        values = self.config.values
        del self.config.values
        domains = self.domains
        del self.domains
        managers = self.detach_managers()
        # remove potentially pickling-problematic values from config
        for key, val in list(vars(self.config).items()):
            if key.startswith('_') or \
               isinstance(val, types.ModuleType) or \
               isinstance(val, types.FunctionType) or \
               isinstance(val, class_types):
                del self.config[key]
        with open(filename, 'wb') as picklefile:
            pickle.dump(self, picklefile, pickle.HIGHEST_PROTOCOL)
        # reset attributes
        self.attach_managers(managers)
        self.domains = domains
        self.config.values = values
        self.set_warnfunc(warnfunc)

    # --------- ENVIRONMENT INITIALIZATION -------------------------------------

    def __init__(self, srcdir, doctreedir, config):
        self.doctreedir = doctreedir
        self.srcdir = srcdir
        self.config = config

        # the method of doctree versioning; see set_versioning_method
        self.versioning_condition = None
        self.versioning_compare = None

        # the application object; only set while update() runs
        self.app = None

        # all the registered domains, set by the application
        self.domains = {}

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
        self.all_docs = {}          # docname -> mtime at the time of reading
                                    # contains all read docnames
        self.dependencies = {}      # docname -> set of dependent file
                                    # names, relative to documentation root
        self.included = set()       # docnames included from other documents
        self.reread_always = set()  # docnames to re-read unconditionally on
                                    # next build

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
        self.toc_fignumbers = {}    # docname -> dict of figtype ->
                                    # dict of figureid -> number

        self.toctree_includes = {}  # docname -> list of toctree includefiles
        self.files_to_rebuild = {}  # docname -> set of files
                                    # (containing its TOCs) to rebuild too
        self.glob_toctrees = set()  # docnames that have :glob: toctrees
        self.numbered_toctrees = set()  # docnames that have :numbered: toctrees

        # domain-specific inventories, here to be pickled
        self.domaindata = {}        # domainname -> domain-specific dict

        # Other inventories
        self.indexentries = {}      # docname -> list of
                                    # (type, string, target, aliasname)
        self.versionchanges = {}    # version -> list of (type, docname,
                                    # lineno, module, descname, content)

        # these map absolute path -> (docnames, unique filename)
        self.images = FilenameUniqDict()
        self.dlfiles = FilenameUniqDict()

        # temporary data storage while reading a document
        self.temp_data = {}
        # context for cross-references (e.g. current module or class)
        # this is similar to temp_data, but will for example be copied to
        # attributes of "any" cross references
        self.ref_context = {}

        self.managers = {}
        self.init_managers()

    def init_managers(self):
        managers = {}
        for manager_class in [IndexEntries, Toctree]:
            managers[manager_class.name] = manager_class(self)
        self.attach_managers(managers)

    def attach_managers(self, managers):
        for name, manager in iteritems(managers):
            self.managers[name] = manager
            manager.attach(self)

    def detach_managers(self):
        managers = self.managers
        self.managers = {}
        for _, manager in iteritems(managers):
            manager.detach(self)
        return managers

    def set_warnfunc(self, func):
        self._warnfunc = func
        self.settings['warning_stream'] = WarningStream(func)

    def set_versioning_method(self, method, compare):
        """This sets the doctree versioning method for this environment.

        Versioning methods are a builder property; only builders with the same
        versioning method can share the same doctree directory.  Therefore, we
        raise an exception if the user tries to use an environment with an
        incompatible versioning method.
        """
        if method not in versioning_conditions:
            raise ValueError('invalid versioning method: %r' % method)
        condition = versioning_conditions[method]
        if self.versioning_condition not in (None, condition):
            raise SphinxError('This environment is incompatible with the '
                              'selected builder, please choose another '
                              'doctree directory.')
        self.versioning_condition = condition
        self.versioning_compare = compare

    def warn(self, docname, msg, lineno=None, **kwargs):
        """Emit a warning.

        This differs from using ``app.warn()`` in that the warning may not
        be emitted instantly, but collected for emitting all warnings after
        the update of the environment.
        """
        # strange argument order is due to backwards compatibility
        self._warnfunc(msg, (docname, lineno), **kwargs)

    def warn_node(self, msg, node, **kwargs):
        """Like :meth:`warn`, but with source information taken from *node*."""
        self._warnfunc(msg, '%s:%s' % get_source_line(node), **kwargs)

    def clear_doc(self, docname):
        """Remove all traces of a source file in the inventory."""
        if docname in self.all_docs:
            self.all_docs.pop(docname, None)
            self.reread_always.discard(docname)
            self.metadata.pop(docname, None)
            self.dependencies.pop(docname, None)
            self.titles.pop(docname, None)
            self.longtitles.pop(docname, None)
            self.images.purge_doc(docname)
            self.dlfiles.purge_doc(docname)

            for version, changes in self.versionchanges.items():
                new = [change for change in changes if change[1] != docname]
                changes[:] = new

        for manager in itervalues(self.managers):
            manager.clear_doc(docname)

        for domain in self.domains.values():
            domain.clear_doc(docname)

    def merge_info_from(self, docnames, other, app):
        """Merge global information gathered about *docnames* while reading them
        from the *other* environment.

        This possibly comes from a parallel build process.
        """
        docnames = set(docnames)
        for docname in docnames:
            self.all_docs[docname] = other.all_docs[docname]
            if docname in other.reread_always:
                self.reread_always.add(docname)
            self.metadata[docname] = other.metadata[docname]
            if docname in other.dependencies:
                self.dependencies[docname] = other.dependencies[docname]
            self.titles[docname] = other.titles[docname]
            self.longtitles[docname] = other.longtitles[docname]

        self.images.merge_other(docnames, other.images)
        self.dlfiles.merge_other(docnames, other.dlfiles)

        for version, changes in other.versionchanges.items():
            self.versionchanges.setdefault(version, []).extend(
                change for change in changes if change[1] in docnames)

        for manager in itervalues(self.managers):
            manager.merge_other(docnames, other)
        for domainname, domain in self.domains.items():
            domain.merge_domaindata(docnames, other.domaindata[domainname])
        app.emit('env-merge-info', self, docnames, other)

    def path2doc(self, filename):
        """Return the docname for the filename if the file is document.

        *filename* should be absolute or relative to the source directory.
        """
        if filename.startswith(self.srcdir):
            filename = filename[len(self.srcdir) + 1:]
        for suffix in self.config.source_suffix:
            if fnmatch.fnmatch(filename, '*' + suffix):
                return filename[:-len(suffix)]
        else:
            # the file does not have docname
            return None

    def doc2path(self, docname, base=True, suffix=None):
        """Return the filename for the document name.

        If *base* is True, return absolute path under self.srcdir.
        If *base* is None, return relative path to self.srcdir.
        If *base* is a path string, return absolute path under that.
        If *suffix* is not None, add it instead of config.source_suffix.
        """
        docname = docname.replace(SEP, path.sep)
        if suffix is None:
            for candidate_suffix in self.config.source_suffix:
                if path.isfile(path.join(self.srcdir, docname) +
                               candidate_suffix):
                    suffix = candidate_suffix
                    break
            else:
                # document does not exist
                suffix = self.config.source_suffix[0]
        if base is True:
            return path.join(self.srcdir, docname) + suffix
        elif base is None:
            return docname + suffix
        else:
            return path.join(base, docname) + suffix

    def relfn2path(self, filename, docname=None):
        """Return paths to a file referenced from a document, relative to
        documentation root and absolute.

        In the input "filename", absolute filenames are taken as relative to the
        source dir, while relative filenames are relative to the dir of the
        containing document.
        """
        if filename.startswith('/') or filename.startswith(os.sep):
            rel_fn = filename[1:]
        else:
            docdir = path.dirname(self.doc2path(docname or self.docname,
                                                base=None))
            rel_fn = path.join(docdir, filename)
        try:
            # the path.abspath() might seem redundant, but otherwise artifacts
            # such as ".." will remain in the path
            return rel_fn, path.abspath(path.join(self.srcdir, rel_fn))
        except UnicodeDecodeError:
            # the source directory is a bytestring with non-ASCII characters;
            # let's try to encode the rel_fn in the file system encoding
            enc_rel_fn = rel_fn.encode(sys.getfilesystemencoding())
            return rel_fn, path.abspath(path.join(self.srcdir, enc_rel_fn))

    def find_files(self, config):
        """Find all source files in the source dir and put them in
        self.found_docs.
        """
        matchers = compile_matchers(
            config.exclude_patterns[:] +
            config.templates_path +
            config.html_extra_path +
            ['**/_sources', '.#*', '**/.#*', '*.lproj/**']
        )
        self.found_docs = set()
        for docname in get_matching_docs(self.srcdir, config.source_suffix,
                                         exclude_matchers=matchers):
            if os.access(self.doc2path(docname), os.R_OK):
                self.found_docs.add(docname)
            else:
                self.warn(docname, "document not readable. Ignored.")

        # add catalog mo file dependency
        for docname in self.found_docs:
            catalog_files = find_catalog_files(
                docname,
                self.srcdir,
                self.config.locale_dirs,
                self.config.language,
                self.config.gettext_compact)
            for filename in catalog_files:
                self.dependencies.setdefault(docname, set()).add(filename)

    def get_outdated_files(self, config_changed):
        """Return (added, changed, removed) sets."""
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
                # check the "reread always" list
                if docname in self.reread_always:
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

    def update(self, config, srcdir, doctreedir, app):
        """(Re-)read all files new or changed since last update.

        Store all environment docnames in the canonical format (ie using SEP as
        a separator in place of os.path.sep).
        """
        config_changed = False
        if self.config is None:
            msg = '[new config] '
            config_changed = True
        else:
            # check if a config value was changed that affects how
            # doctrees are read
            for key, descr in iteritems(config.values):
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

        # this cache also needs to be updated every time
        self._nitpick_ignore = set(self.config.nitpick_ignore)

        app.info(bold('updating environment: '), nonl=1)

        added, changed, removed = self.get_outdated_files(config_changed)

        # allow user intervention as well
        for docs in app.emit('env-get-outdated', self, added, changed, removed):
            changed.update(set(docs) & self.found_docs)

        # if files were added or removed, all documents with globbed toctrees
        # must be reread
        if added or removed:
            # ... but not those that already were removed
            changed.update(self.glob_toctrees & self.found_docs)

        msg += '%s added, %s changed, %s removed' % (len(added), len(changed),
                                                     len(removed))
        app.info(msg)

        self.app = app

        # clear all files no longer present
        for docname in removed:
            app.emit('env-purge-doc', self, docname)
            self.clear_doc(docname)

        # read all new and changed files
        docnames = sorted(added | changed)
        # allow changing and reordering the list of docs to read
        app.emit('env-before-read-docs', self, docnames)

        # check if we should do parallel or serial read
        par_ok = False
        if parallel_available and len(docnames) > 5 and app.parallel > 1:
            par_ok = True
            for extname, md in app._extension_metadata.items():
                ext_ok = md.get('parallel_read_safe')
                if ext_ok:
                    continue
                if ext_ok is None:
                    app.warn('the %s extension does not declare if it '
                             'is safe for parallel reading, assuming it '
                             'isn\'t - please ask the extension author to '
                             'check and make it explicit' % extname)
                    app.warn('doing serial read')
                else:
                    app.warn('the %s extension is not safe for parallel '
                             'reading, doing serial read' % extname)
                par_ok = False
                break
        if par_ok:
            self._read_parallel(docnames, app, nproc=app.parallel)
        else:
            self._read_serial(docnames, app)

        if config.master_doc not in self.all_docs:
            raise SphinxError('master file %s not found' %
                              self.doc2path(config.master_doc))

        self.app = None

        for retval in app.emit('env-updated', self):
            if retval is not None:
                docnames.extend(retval)

        return sorted(docnames)

    def _read_serial(self, docnames, app):
        for docname in app.status_iterator(docnames, 'reading sources... ',
                                           purple, len(docnames)):
            # remove all inventory entries for that file
            app.emit('env-purge-doc', self, docname)
            self.clear_doc(docname)
            self.read_doc(docname, app)

    def _read_parallel(self, docnames, app, nproc):
        # clear all outdated docs at once
        for docname in docnames:
            app.emit('env-purge-doc', self, docname)
            self.clear_doc(docname)

        def read_process(docs):
            self.app = app
            self.warnings = []
            self.set_warnfunc(lambda *args, **kwargs: self.warnings.append((args, kwargs)))
            for docname in docs:
                self.read_doc(docname, app)
            # allow pickling self to send it back
            self.set_warnfunc(None)
            del self.app
            del self.domains
            del self.config.values
            del self.config
            return self

        def merge(docs, otherenv):
            warnings.extend(otherenv.warnings)
            self.merge_info_from(docs, otherenv, app)

        tasks = ParallelTasks(nproc)
        chunks = make_chunks(docnames, nproc)

        warnings = []
        for chunk in app.status_iterator(
                chunks, 'reading sources... ', purple, len(chunks)):
            tasks.add_task(read_process, chunk, merge)

        # make sure all threads have finished
        app.info(bold('waiting for workers...'))
        tasks.join()

        for warning, kwargs in warnings:
            self._warnfunc(*warning, **kwargs)

    def check_dependents(self, already):
        to_rewrite = (self.toctree.assign_section_numbers() +
                      self.toctree.assign_figure_numbers())
        for docname in set(to_rewrite):
            if docname not in already:
                yield docname

    # --------- SINGLE FILE READING --------------------------------------------

    def warn_and_replace(self, error):
        """Custom decoding error handler that warns and replaces."""
        linestart = error.object.rfind(b'\n', 0, error.start)
        lineend = error.object.find(b'\n', error.start)
        if lineend == -1:
            lineend = len(error.object)
        lineno = error.object.count(b'\n', 0, error.start) + 1
        self.warn(self.docname, 'undecodable source characters, '
                  'replacing with "?": %r' %
                  (error.object[linestart+1:error.start] + b'>>>' +
                   error.object[error.start:error.end] + b'<<<' +
                   error.object[error.end:lineend]), lineno)
        return (u'?', error.end)

    def read_doc(self, docname, app=None):
        """Parse a file and add/update inventory entries for the doctree."""

        self.temp_data['docname'] = docname
        # defaults to the global default, but can be re-set in a document
        self.temp_data['default_domain'] = \
            self.domains.get(self.config.primary_domain)

        self.settings['input_encoding'] = self.config.source_encoding
        self.settings['trim_footnote_reference_space'] = \
            self.config.trim_footnote_reference_space
        self.settings['gettext_compact'] = self.config.gettext_compact

        docutilsconf = path.join(self.srcdir, 'docutils.conf')
        # read docutils.conf from source dir, not from current dir
        OptionParser.standard_config_files[1] = docutilsconf
        if path.isfile(docutilsconf):
            self.note_dependency(docutilsconf)

        with sphinx_domains(self):
            if self.config.default_role:
                role_fn, messages = roles.role(self.config.default_role, english,
                                               0, dummy_reporter)
                if role_fn:
                    roles._roles[''] = role_fn
                else:
                    self.warn(docname, 'default role %s not found' %
                              self.config.default_role)

            codecs.register_error('sphinx', self.warn_and_replace)

            # publish manually
            reader = SphinxStandaloneReader(self.app, parsers=self.config.source_parsers)
            pub = Publisher(reader=reader,
                            writer=SphinxDummyWriter(),
                            destination_class=NullOutput)
            pub.set_components(None, 'restructuredtext', None)
            pub.process_programmatic_settings(None, self.settings, None)
            src_path = self.doc2path(docname)
            source = SphinxFileInput(app, self, source=None, source_path=src_path,
                                     encoding=self.config.source_encoding)
            pub.source = source
            pub.settings._source = src_path
            pub.set_destination(None, None)
            pub.publish()
            doctree = pub.document

        # post-processing
        self.process_dependencies(docname, doctree)
        self.process_images(docname, doctree)
        self.process_downloads(docname, doctree)
        self.process_metadata(docname, doctree)
        self.create_title_from(docname, doctree)
        for manager in itervalues(self.managers):
            manager.process_doc(docname, doctree)
        for domain in itervalues(self.domains):
            domain.process_doc(self, docname, doctree)

        # allow extension-specific post-processing
        if app:
            app.emit('doctree-read', doctree)

        # store time of reading, for outdated files detection
        # (Some filesystems have coarse timestamp resolution;
        # therefore time.time() can be older than filesystem's timestamp.
        # For example, FAT32 has 2sec timestamp resolution.)
        self.all_docs[docname] = max(
            time.time(), path.getmtime(self.doc2path(docname)))

        if self.versioning_condition:
            old_doctree = None
            if self.versioning_compare:
                # get old doctree
                try:
                    with open(self.doc2path(docname,
                                            self.doctreedir, '.doctree'), 'rb') as f:
                        old_doctree = pickle.load(f)
                except EnvironmentError:
                    pass

            # add uids for versioning
            if not self.versioning_compare or old_doctree is None:
                list(add_uids(doctree, self.versioning_condition))
            else:
                list(merge_doctrees(
                    old_doctree, doctree, self.versioning_condition))

        # make it picklable
        doctree.reporter = None
        doctree.transformer = None
        doctree.settings.warning_stream = None
        doctree.settings.env = None
        doctree.settings.record_dependencies = None

        # cleanup
        self.temp_data.clear()
        self.ref_context.clear()
        roles._roles.pop('', None)  # if a document has set a local default role

        # save the parsed doctree
        doctree_filename = self.doc2path(docname, self.doctreedir,
                                         '.doctree')
        ensuredir(path.dirname(doctree_filename))
        with open(doctree_filename, 'wb') as f:
            pickle.dump(doctree, f, pickle.HIGHEST_PROTOCOL)

    # utilities to use while reading a document

    @property
    def docname(self):
        """Returns the docname of the document currently being parsed."""
        return self.temp_data['docname']

    @property
    def currmodule(self):
        """Backwards compatible alias.  Will be removed."""
        self.warn(self.docname, 'env.currmodule is being referenced by an '
                  'extension; this API will be removed in the future')
        return self.ref_context.get('py:module')

    @property
    def currclass(self):
        """Backwards compatible alias.  Will be removed."""
        self.warn(self.docname, 'env.currclass is being referenced by an '
                  'extension; this API will be removed in the future')
        return self.ref_context.get('py:class')

    def new_serialno(self, category=''):
        """Return a serial number, e.g. for index entry targets.

        The number is guaranteed to be unique in the current document.
        """
        key = category + 'serialno'
        cur = self.temp_data.get(key, 0)
        self.temp_data[key] = cur + 1
        return cur

    def note_dependency(self, filename):
        """Add *filename* as a dependency of the current document.

        This means that the document will be rebuilt if this file changes.

        *filename* should be absolute or relative to the source directory.
        """
        self.dependencies.setdefault(self.docname, set()).add(filename)

    def note_included(self, filename):
        """Add *filename* as a included from other document.

        This means the document is not orphaned.

        *filename* should be absolute or relative to the source directory.
        """
        self.included.add(self.path2doc(filename))

    def note_reread(self):
        """Add the current document to the list of documents that will
        automatically be re-read at the next build.
        """
        self.reread_always.add(self.docname)

    def note_versionchange(self, type, version, node, lineno):
        self.versionchanges.setdefault(version, []).append(
            (type, self.temp_data['docname'], lineno,
             self.ref_context.get('py:module'),
             self.temp_data.get('object'), node.astext()))

    # post-processing of read doctrees

    def process_dependencies(self, docname, doctree):
        """Process docutils-generated dependency info."""
        cwd = getcwd()
        frompath = path.join(path.normpath(self.srcdir), 'dummy')
        deps = doctree.settings.record_dependencies
        if not deps:
            return
        for dep in deps.list:
            # the dependency path is relative to the working dir, so get
            # one relative to the srcdir
            if isinstance(dep, bytes):
                dep = dep.decode(fs_encoding)
            relpath = relative_path(frompath,
                                    path.normpath(path.join(cwd, dep)))
            self.dependencies.setdefault(docname, set()).add(relpath)

    def process_downloads(self, docname, doctree):
        """Process downloadable file paths. """
        for node in doctree.traverse(addnodes.download_reference):
            targetname = node['reftarget']
            rel_filename, filename = self.relfn2path(targetname, docname)
            self.dependencies.setdefault(docname, set()).add(rel_filename)
            if not os.access(filename, os.R_OK):
                self.warn_node('download file not readable: %s' % filename,
                               node)
                continue
            uniquename = self.dlfiles.add_file(docname, filename)
            node['filename'] = uniquename

    def process_images(self, docname, doctree):
        """Process and rewrite image URIs."""
        def collect_candidates(imgpath, candidates):
            globbed = {}
            for filename in glob(imgpath):
                new_imgpath = relative_path(path.join(self.srcdir, 'dummy'),
                                            filename)
                try:
                    mimetype = guess_mimetype(filename)
                    if mimetype not in candidates:
                        globbed.setdefault(mimetype, []).append(new_imgpath)
                except (OSError, IOError) as err:
                    self.warn_node('image file %s not readable: %s' %
                                   (filename, err), node)
            for key, files in iteritems(globbed):
                candidates[key] = sorted(files, key=len)[0]  # select by similarity

        for node in doctree.traverse(nodes.image):
            # Map the mimetype to the corresponding image.  The writer may
            # choose the best image from these candidates.  The special key * is
            # set if there is only single candidate to be used by a writer.
            # The special key ? is set for nonlocal URIs.
            node['candidates'] = candidates = {}
            imguri = node['uri']
            if imguri.startswith('data:'):
                self.warn_node('image data URI found. some builders might not support', node,
                               type='image', subtype='data_uri')
                candidates['?'] = imguri
                continue
            elif imguri.find('://') != -1:
                self.warn_node('nonlocal image URI found: %s' % imguri, node,
                               type='image', subtype='nonlocal_uri')
                candidates['?'] = imguri
                continue
            rel_imgpath, full_imgpath = self.relfn2path(imguri, docname)
            if self.config.language:
                # substitute figures (ex. foo.png -> foo.en.png)
                i18n_full_imgpath = search_image_for_language(full_imgpath, self)
                if i18n_full_imgpath != full_imgpath:
                    full_imgpath = i18n_full_imgpath
                    rel_imgpath = relative_path(path.join(self.srcdir, 'dummy'),
                                                i18n_full_imgpath)
            # set imgpath as default URI
            node['uri'] = rel_imgpath
            if rel_imgpath.endswith(os.extsep + '*'):
                if self.config.language:
                    # Search language-specific figures at first
                    i18n_imguri = get_image_filename_for_language(imguri, self)
                    _, full_i18n_imgpath = self.relfn2path(i18n_imguri, docname)
                    collect_candidates(full_i18n_imgpath, candidates)

                collect_candidates(full_imgpath, candidates)
            else:
                candidates['*'] = rel_imgpath

            # map image paths to unique image names (so that they can be put
            # into a single directory)
            for imgpath in itervalues(candidates):
                self.dependencies.setdefault(docname, set()).add(imgpath)
                if not os.access(path.join(self.srcdir, imgpath), os.R_OK):
                    self.warn_node('image file not readable: %s' % imgpath,
                                   node)
                    continue
                self.images.add_file(docname, imgpath)

    def process_metadata(self, docname, doctree):
        """Process the docinfo part of the doctree as metadata.

        Keep processing minimal -- just return what docutils says.
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
            # nodes are multiply inherited...
            if isinstance(node, nodes.authors):
                md['authors'] = [author.astext() for author in node]
            elif isinstance(node, nodes.TextElement):  # e.g. author
                md[node.__class__.__name__] = node.astext()
            else:
                name, body = node
                md[name.astext()] = body.astext()
        for name, value in md.items():
            if name in ('tocdepth',):
                try:
                    value = int(value)
                except ValueError:
                    value = 0
                md[name] = value

        del doctree[0]

    def create_title_from(self, docname, document):
        """Add a title node to the document (just copy the first section title),
        and store that title in the environment.
        """
        titlenode = nodes.title()
        longtitlenode = titlenode
        # explicit title set with title directive; use this only for
        # the <title> tag in HTML output
        if 'title' in document:
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

    def note_toctree(self, docname, toctreenode):
        """Note a TOC tree directive in a document and gather information about
        file relations from it.
        """
        self.toctree.note_toctree(docname, toctreenode)

    def get_toc_for(self, docname, builder):
        """Return a TOC nodetree -- for use on the same page only!"""
        return self.toctree.get_toc_for(docname, builder)

    def get_toctree_for(self, docname, builder, collapse, **kwds):
        """Return the global TOC nodetree."""
        return self.toctree.get_toctree_for(docname, builder, collapse, **kwds)

    def get_domain(self, domainname):
        """Return the domain instance with the specified name.

        Raises an ExtensionError if the domain is not registered.
        """
        try:
            return self.domains[domainname]
        except KeyError:
            raise ExtensionError('Domain %r is not registered' % domainname)

    # --------- RESOLVING REFERENCES AND TOCTREES ------------------------------

    def get_doctree(self, docname):
        """Read the doctree for a file from the pickle and return it."""
        doctree_filename = self.doc2path(docname, self.doctreedir, '.doctree')
        with open(doctree_filename, 'rb') as f:
            doctree = pickle.load(f)
        doctree.settings.env = self
        doctree.reporter = Reporter(self.doc2path(docname), 2, 5,
                                    stream=WarningStream(self._warnfunc))
        return doctree

    def get_and_resolve_doctree(self, docname, builder, doctree=None,
                                prune_toctrees=True, includehidden=False):
        """Read the doctree from the pickle, resolve cross-references and
        toctrees and return it.
        """
        if doctree is None:
            doctree = self.get_doctree(docname)

        # resolve all pending cross-references
        self.resolve_references(doctree, docname, builder)

        # now, resolve all toctree nodes
        for toctreenode in doctree.traverse(addnodes.toctree):
            result = self.resolve_toctree(docname, builder, toctreenode,
                                          prune=prune_toctrees,
                                          includehidden=includehidden)
            if result is None:
                toctreenode.replace_self([])
            else:
                toctreenode.replace_self(result)

        return doctree

    def resolve_toctree(self, docname, builder, toctree, prune=True, maxdepth=0,
                        titles_only=False, collapse=False, includehidden=False):
        """Resolve a *toctree* node into individual bullet lists with titles
        as items, returning None (if no containing titles are found) or
        a new node.

        If *prune* is True, the tree is pruned to *maxdepth*, or if that is 0,
        to the value of the *maxdepth* option on the *toctree* node.
        If *titles_only* is True, only toplevel document titles will be in the
        resulting tree.
        If *collapse* is True, all branches not containing docname will
        be collapsed.
        """
        return self.toctree.resolve_toctree(docname, builder, toctree, prune,
                                            maxdepth, titles_only, collapse,
                                            includehidden)

    def resolve_references(self, doctree, fromdocname, builder):
        for node in doctree.traverse(addnodes.pending_xref):
            contnode = node[0].deepcopy()
            newnode = None

            typ = node['reftype']
            target = node['reftarget']
            refdoc = node.get('refdoc', fromdocname)
            domain = None

            try:
                if 'refdomain' in node and node['refdomain']:
                    # let the domain try to resolve the reference
                    try:
                        domain = self.domains[node['refdomain']]
                    except KeyError:
                        raise NoUri
                    newnode = domain.resolve_xref(self, refdoc, builder,
                                                  typ, target, node, contnode)
                # really hardwired reference types
                elif typ == 'any':
                    newnode = self._resolve_any_reference(builder, refdoc, node, contnode)
                elif typ == 'doc':
                    newnode = self._resolve_doc_reference(builder, refdoc, node, contnode)
                # no new node found? try the missing-reference event
                if newnode is None:
                    newnode = builder.app.emit_firstresult(
                        'missing-reference', self, node, contnode)
                    # still not found? warn if node wishes to be warned about or
                    # we are in nit-picky mode
                    if newnode is None:
                        self._warn_missing_reference(refdoc, typ, target, node, domain)
            except NoUri:
                newnode = contnode
            node.replace_self(newnode or contnode)

        # remove only-nodes that do not belong to our builder
        process_only_nodes(doctree, builder.tags, warn_node=self.warn_node)

        # allow custom references to be resolved
        builder.app.emit('doctree-resolved', doctree, fromdocname)

    def _warn_missing_reference(self, refdoc, typ, target, node, domain):
        warn = node.get('refwarn')
        if self.config.nitpicky:
            warn = True
            if self._nitpick_ignore:
                dtype = domain and '%s:%s' % (domain.name, typ) or typ
                if (dtype, target) in self._nitpick_ignore:
                    warn = False
                # for "std" types also try without domain name
                if (not domain or domain.name == 'std') and \
                   (typ, target) in self._nitpick_ignore:
                    warn = False
        if not warn:
            return
        if domain and typ in domain.dangling_warnings:
            msg = domain.dangling_warnings[typ]
        elif typ == 'doc':
            msg = 'unknown document: %(target)s'
        elif node.get('refdomain', 'std') not in ('', 'std'):
            msg = '%s:%s reference target not found: %%(target)s' % \
                  (node['refdomain'], typ)
        else:
            msg = '%r reference target not found: %%(target)s' % typ
        self.warn_node(msg % {'target': target}, node, type='ref', subtype=typ)

    def _resolve_doc_reference(self, builder, refdoc, node, contnode):
        # directly reference to document by source name;
        # can be absolute or relative
        docname = docname_join(refdoc, node['reftarget'])
        if docname in self.all_docs:
            if node['refexplicit']:
                # reference with explicit title
                caption = node.astext()
            else:
                caption = clean_astext(self.titles[docname])
            innernode = nodes.inline(caption, caption)
            innernode['classes'].append('doc')
            newnode = nodes.reference('', '', internal=True)
            newnode['refuri'] = builder.get_relative_uri(refdoc, docname)
            newnode.append(innernode)
            return newnode

    def _resolve_any_reference(self, builder, refdoc, node, contnode):
        """Resolve reference generated by the "any" role."""
        target = node['reftarget']
        results = []
        # first, try resolving as :doc:
        doc_ref = self._resolve_doc_reference(builder, refdoc, node, contnode)
        if doc_ref:
            results.append(('doc', doc_ref))
        # next, do the standard domain (makes this a priority)
        results.extend(self.domains['std'].resolve_any_xref(
            self, refdoc, builder, target, node, contnode))
        for domain in self.domains.values():
            if domain.name == 'std':
                continue  # we did this one already
            try:
                results.extend(domain.resolve_any_xref(self, refdoc, builder,
                                                       target, node, contnode))
            except NotImplementedError:
                # the domain doesn't yet support the new interface
                # we have to manually collect possible references (SLOW)
                for role in domain.roles:
                    res = domain.resolve_xref(self, refdoc, builder, role, target,
                                              node, contnode)
                    if res and isinstance(res[0], nodes.Element):
                        results.append(('%s:%s' % (domain.name, role), res))
        # now, see how many matches we got...
        if not results:
            return None
        if len(results) > 1:
            nice_results = ' or '.join(':%s:' % r[0] for r in results)
            self.warn_node('more than one target found for \'any\' cross-'
                           'reference %r: could be %s' % (target, nice_results),
                           node)
        res_role, newnode = results[0]
        # Override "any" class with the actual role type to get the styling
        # approximately correct.
        res_domain = res_role.split(':')[0]
        if newnode and newnode[0].get('classes'):
            newnode[0]['classes'].append(res_domain)
            newnode[0]['classes'].append(res_role.replace(':', '-'))
        return newnode

    def create_index(self, builder, group_entries=True,
                     _fixre=re.compile(r'(.*) ([(][^()]*[)])')):
        return self.indices.create_index(builder, group_entries=group_entries, _fixre=_fixre)

    def collect_relations(self):
        traversed = set()

        def traverse_toctree(parent, docname):
            if parent == docname:
                self.warn(docname, 'self referenced toctree found. Ignored.')
                return

            # traverse toctree by pre-order
            yield parent, docname
            traversed.add(docname)

            for child in (self.toctree_includes.get(docname) or []):
                for subparent, subdocname in traverse_toctree(docname, child):
                    if subdocname not in traversed:
                        yield subparent, subdocname
                        traversed.add(subdocname)

        relations = {}
        docnames = traverse_toctree(None, self.config.master_doc)
        prevdoc = None
        parent, docname = next(docnames)
        for nextparent, nextdoc in docnames:
            relations[docname] = [parent, prevdoc, nextdoc]
            prevdoc = docname
            docname = nextdoc
            parent = nextparent

        relations[docname] = [parent, prevdoc, None]

        return relations

    def check_consistency(self):
        """Do consistency checks."""
        for docname in sorted(self.all_docs):
            if docname not in self.files_to_rebuild:
                if docname == self.config.master_doc:
                    # the master file is not included anywhere ;)
                    continue
                if docname in self.included:
                    # the document is included from other documents
                    continue
                if 'orphan' in self.metadata[docname]:
                    continue
                self.warn(docname, 'document isn\'t included in any toctree')
