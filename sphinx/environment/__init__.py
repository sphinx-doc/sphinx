"""
    sphinx.environment
    ~~~~~~~~~~~~~~~~~~

    Global creation environment.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import pickle
import warnings
from collections import defaultdict
from copy import copy
from io import BytesIO
from os import path
from typing import Any, Callable, Dict, Generator, IO, Iterator, List, Set, Tuple, Union

from docutils import nodes
from docutils.nodes import Node

from sphinx import addnodes
from sphinx.config import Config
from sphinx.deprecation import (
    RemovedInSphinx30Warning, RemovedInSphinx40Warning, deprecated_alias
)
from sphinx.domains import Domain
from sphinx.environment.adapters.toctree import TocTree
from sphinx.errors import SphinxError, BuildEnvironmentError, DocumentError, ExtensionError
from sphinx.events import EventManager
from sphinx.locale import __
from sphinx.project import Project
from sphinx.transforms import SphinxTransformer
from sphinx.util import DownloadFiles, FilenameUniqDict
from sphinx.util import logging
from sphinx.util.docutils import LoggingReporter
from sphinx.util.i18n import CatalogRepository, docname_to_domain
from sphinx.util.nodes import is_translatable

if False:
    # For type annotation
    from sphinx.application import Sphinx
    from sphinx.builders import Builder

logger = logging.getLogger(__name__)

default_settings = {
    'embed_stylesheet': False,
    'cloak_email_addresses': True,
    'pep_base_url': 'https://www.python.org/dev/peps/',
    'pep_references': None,
    'rfc_base_url': 'https://tools.ietf.org/html/',
    'rfc_references': None,
    'input_encoding': 'utf-8-sig',
    'doctitle_xform': False,
    'sectsubtitle_xform': False,
    'halt_level': 5,
    'file_insertion_enabled': True,
    'smartquotes_locales': [],
}  # type: Dict[str, Any]

# This is increased every time an environment attribute is added
# or changed to properly invalidate pickle files.
ENV_VERSION = 56

# config status
CONFIG_OK = 1
CONFIG_NEW = 2
CONFIG_CHANGED = 3
CONFIG_EXTENSIONS_CHANGED = 4

CONFIG_CHANGED_REASON = {
    CONFIG_NEW: __('new config'),
    CONFIG_CHANGED: __('config changed'),
    CONFIG_EXTENSIONS_CHANGED: __('extensions changed'),
}


versioning_conditions = {
    'none': False,
    'text': is_translatable,
}  # type: Dict[str, Union[bool, Callable]]


class BuildEnvironment:
    """
    The environment in which the ReST files are translated.
    Stores an inventory of cross-file targets and provides doctree
    transformations to resolve links to them.
    """

    domains = None  # type: Dict[str, Domain]

    # --------- ENVIRONMENT INITIALIZATION -------------------------------------

    def __init__(self, app: "Sphinx" = None):
        self.app = None                  # type: Sphinx
        self.doctreedir = None           # type: str
        self.srcdir = None               # type: str
        self.config = None               # type: Config
        self.config_status = None        # type: int
        self.config_status_extra = None  # type: str
        self.events = None               # type: EventManager
        self.project = None              # type: Project
        self.version = None              # type: Dict[str, str]

        # the method of doctree versioning; see set_versioning_method
        self.versioning_condition = None  # type: Union[bool, Callable]
        self.versioning_compare = None  # type: bool

        # all the registered domains, set by the application
        self.domains = {}

        # the docutils settings for building
        self.settings = default_settings.copy()
        self.settings['env'] = self

        # All "docnames" here are /-separated and relative and exclude
        # the source suffix.

        self.all_docs = {}          # type: Dict[str, float]
                                    # docname -> mtime at the time of reading
                                    # contains all read docnames
        self.dependencies = defaultdict(set)    # type: Dict[str, Set[str]]
                                    # docname -> set of dependent file
                                    # names, relative to documentation root
        self.included = defaultdict(set)        # type: Dict[str, Set[str]]
                                    # docname -> set of included file
                                    # docnames included from other documents
        self.reread_always = set()  # type: Set[str]
                                    # docnames to re-read unconditionally on
                                    # next build

        # File metadata
        self.metadata = defaultdict(dict)       # type: Dict[str, Dict[str, Any]]
                                                # docname -> dict of metadata items

        # TOC inventory
        self.titles = {}            # type: Dict[str, nodes.title]
                                    # docname -> title node
        self.longtitles = {}        # type: Dict[str, nodes.title]
                                    # docname -> title node; only different if
                                    # set differently with title directive
        self.tocs = {}              # type: Dict[str, nodes.bullet_list]
                                    # docname -> table of contents nodetree
        self.toc_num_entries = {}   # type: Dict[str, int]
                                    # docname -> number of real entries

        # used to determine when to show the TOC
        # in a sidebar (don't show if it's only one item)
        self.toc_secnumbers = {}    # type: Dict[str, Dict[str, Tuple[int, ...]]]
                                    # docname -> dict of sectionid -> number
        self.toc_fignumbers = {}    # type: Dict[str, Dict[str, Dict[str, Tuple[int, ...]]]]
                                    # docname -> dict of figtype ->
                                    # dict of figureid -> number

        self.toctree_includes = {}  # type: Dict[str, List[str]]
                                    # docname -> list of toctree includefiles
        self.files_to_rebuild = {}  # type: Dict[str, Set[str]]
                                    # docname -> set of files
                                    # (containing its TOCs) to rebuild too
        self.glob_toctrees = set()  # type: Set[str]
                                    # docnames that have :glob: toctrees
        self.numbered_toctrees = set()  # type: Set[str]
                                        # docnames that have :numbered: toctrees

        # domain-specific inventories, here to be pickled
        self.domaindata = {}        # type: Dict[str, Dict]
                                    # domainname -> domain-specific dict

        # Other inventories
        self.indexentries = {}      # type: Dict[str, List[Tuple[str, str, str, str, str]]]
                                    # docname -> list of
                                    # (type, str, target, aliasname)

        # these map absolute path -> (docnames, unique filename)
        self.images = FilenameUniqDict()    # type: FilenameUniqDict
        self.dlfiles = DownloadFiles()      # type: DownloadFiles
                                            # filename -> (set of docnames, destination)

        # the original URI for images
        self.original_image_uri = {}  # type: Dict[str, str]

        # temporary data storage while reading a document
        self.temp_data = {}         # type: Dict[str, Any]
        # context for cross-references (e.g. current module or class)
        # this is similar to temp_data, but will for example be copied to
        # attributes of "any" cross references
        self.ref_context = {}       # type: Dict[str, Any]

        # set up environment
        if app:
            self.setup(app)

    def __getstate__(self) -> Dict:
        """Obtains serializable data for pickling."""
        __dict__ = self.__dict__.copy()
        __dict__.update(app=None, domains={}, events=None)  # clear unpickable attributes
        return __dict__

    def __setstate__(self, state: Dict) -> None:
        self.__dict__.update(state)

    def setup(self, app: "Sphinx") -> None:
        """Set up BuildEnvironment object."""
        if self.version and self.version != app.registry.get_envversion(app):
            raise BuildEnvironmentError(__('build environment version not current'))
        elif self.srcdir and self.srcdir != app.srcdir:
            raise BuildEnvironmentError(__('source directory has changed'))

        if self.project:
            app.project.restore(self.project)

        self.app = app
        self.doctreedir = app.doctreedir
        self.events = app.events
        self.srcdir = app.srcdir
        self.project = app.project
        self.version = app.registry.get_envversion(app)

        # initialize domains
        self.domains = {}
        for domain in app.registry.create_domains(self):
            self.domains[domain.name] = domain

        # initialize config
        self._update_config(app.config)

        # initialie settings
        self._update_settings(app.config)

    def _update_config(self, config: Config) -> None:
        """Update configurations by new one."""
        self.config_status = CONFIG_OK
        self.config_status_extra = ''
        if self.config is None:
            self.config_status = CONFIG_NEW
        elif self.config.extensions != config.extensions:
            self.config_status = CONFIG_EXTENSIONS_CHANGED
            extensions = sorted(
                set(self.config.extensions) ^ set(config.extensions))
            if len(extensions) == 1:
                extension = extensions[0]
            else:
                extension = '%d' % (len(extensions),)
            self.config_status_extra = ' (%r)' % (extension,)
        else:
            # check if a config value was changed that affects how
            # doctrees are read
            for item in config.filter('env'):
                if self.config[item.name] != item.value:
                    self.config_status = CONFIG_CHANGED
                    self.config_status_extra = ' (%r)' % (item.name,)
                    break

        self.config = config

    def _update_settings(self, config: Config) -> None:
        """Update settings by new config."""
        self.settings['input_encoding'] = config.source_encoding
        self.settings['trim_footnote_reference_space'] = config.trim_footnote_reference_space
        self.settings['language_code'] = config.language or 'en'

        # Allow to disable by 3rd party extension (workaround)
        self.settings.setdefault('smart_quotes', True)

    def set_versioning_method(self, method: Union[str, Callable], compare: bool) -> None:
        """This sets the doctree versioning method for this environment.

        Versioning methods are a builder property; only builders with the same
        versioning method can share the same doctree directory.  Therefore, we
        raise an exception if the user tries to use an environment with an
        incompatible versioning method.
        """
        condition = None  # type: Union[bool, Callable]
        if callable(method):
            condition = method
        else:
            if method not in versioning_conditions:
                raise ValueError('invalid versioning method: %r' % method)
            condition = versioning_conditions[method]

        if self.versioning_condition not in (None, condition):
            raise SphinxError(__('This environment is incompatible with the '
                                 'selected builder, please choose another '
                                 'doctree directory.'))
        self.versioning_condition = condition
        self.versioning_compare = compare

    def clear_doc(self, docname: str) -> None:
        """Remove all traces of a source file in the inventory."""
        if docname in self.all_docs:
            self.all_docs.pop(docname, None)
            self.included.pop(docname, None)
            self.reread_always.discard(docname)

        for domain in self.domains.values():
            domain.clear_doc(docname)

    def merge_info_from(self, docnames: List[str], other: "BuildEnvironment",
                        app: "Sphinx") -> None:
        """Merge global information gathered about *docnames* while reading them
        from the *other* environment.

        This possibly comes from a parallel build process.
        """
        docnames = set(docnames)  # type: ignore
        for docname in docnames:
            self.all_docs[docname] = other.all_docs[docname]
            self.included[docname] = other.included[docname]
            if docname in other.reread_always:
                self.reread_always.add(docname)

        for domainname, domain in self.domains.items():
            domain.merge_domaindata(docnames, other.domaindata[domainname])
        self.events.emit('env-merge-info', self, docnames, other)

    def path2doc(self, filename: str) -> str:
        """Return the docname for the filename if the file is document.

        *filename* should be absolute or relative to the source directory.
        """
        return self.project.path2doc(filename)

    def doc2path(self, docname: str, base: Union[bool, str] = True, suffix: str = None) -> str:
        """Return the filename for the document name.

        If *base* is True, return absolute path under self.srcdir.
        If *base* is None, return relative path to self.srcdir.
        If *base* is a path string, return absolute path under that.
        If *suffix* is not None, add it instead of config.source_suffix.
        """
        if suffix:
            warnings.warn('The suffix argument for doc2path() is deprecated.',
                          RemovedInSphinx40Warning)
        if base not in (True, None):
            warnings.warn('The string style base argument for doc2path() is deprecated.',
                          RemovedInSphinx40Warning)

        pathname = self.project.doc2path(docname, base is True)
        if suffix:
            filename, _ = path.splitext(pathname)
            pathname = filename + suffix
        if base and base is not True:
            pathname = path.join(base, pathname)  # type: ignore
        return pathname

    def relfn2path(self, filename: str, docname: str = None) -> Tuple[str, str]:
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
        # the path.abspath() might seem redundant, but otherwise artifacts
        # such as ".." will remain in the path
        return rel_fn, path.abspath(path.join(self.srcdir, rel_fn))

    @property
    def found_docs(self) -> Set[str]:
        """contains all existing docnames."""
        return self.project.docnames

    def find_files(self, config: Config, builder: "Builder") -> None:
        """Find all source files in the source dir and put them in
        self.found_docs.
        """
        try:
            exclude_paths = (self.config.exclude_patterns +
                             self.config.templates_path +
                             builder.get_asset_paths())
            self.project.discover(exclude_paths)

            # Current implementation is applying translated messages in the reading
            # phase.Therefore, in order to apply the updated message catalog, it is
            # necessary to re-process from the reading phase. Here, if dependency
            # is set for the doc source and the mo file, it is processed again from
            # the reading phase when mo is updated. In the future, we would like to
            # move i18n process into the writing phase, and remove these lines.
            if builder.use_message_catalog:
                # add catalog mo file dependency
                repo = CatalogRepository(self.srcdir, self.config.locale_dirs,
                                         self.config.language, self.config.source_encoding)
                for docname in self.found_docs:
                    domain = docname_to_domain(docname, self.config.gettext_compact)
                    for catalog in repo.catalogs:
                        if catalog.domain == domain:
                            self.dependencies[docname].add(catalog.mo_path)
        except OSError as exc:
            raise DocumentError(__('Failed to scan documents in %s: %r') % (self.srcdir, exc))

    def get_outdated_files(self, config_changed: bool) -> Tuple[Set[str], Set[str], Set[str]]:
        """Return (added, changed, removed) sets."""
        # clear all files no longer present
        removed = set(self.all_docs) - self.found_docs

        added = set()  # type: Set[str]
        changed = set()  # type: Set[str]

        if config_changed:
            # config values affect e.g. substitutions
            added = self.found_docs
        else:
            for docname in self.found_docs:
                if docname not in self.all_docs:
                    added.add(docname)
                    continue
                # if the doctree file is not there, rebuild
                filename = path.join(self.doctreedir, docname + '.doctree')
                if not path.isfile(filename):
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
                for dep in self.dependencies[docname]:
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
                    except OSError:
                        # give it another chance
                        changed.add(docname)
                        break

        return added, changed, removed

    def check_dependents(self, app: "Sphinx", already: Set[str]) -> Generator[str, None, None]:
        to_rewrite = []  # type: List[str]
        for docnames in self.events.emit('env-get-updated', self):
            to_rewrite.extend(docnames)
        for docname in set(to_rewrite):
            if docname not in already:
                yield docname

    # --------- SINGLE FILE READING --------------------------------------------

    def prepare_settings(self, docname: str) -> None:
        """Prepare to set up environment for reading."""
        self.temp_data['docname'] = docname
        # defaults to the global default, but can be re-set in a document
        self.temp_data['default_role'] = self.config.default_role
        self.temp_data['default_domain'] = \
            self.domains.get(self.config.primary_domain)

    # utilities to use while reading a document

    @property
    def docname(self) -> str:
        """Returns the docname of the document currently being parsed."""
        return self.temp_data['docname']

    def new_serialno(self, category: str = '') -> int:
        """Return a serial number, e.g. for index entry targets.

        The number is guaranteed to be unique in the current document.
        """
        key = category + 'serialno'
        cur = self.temp_data.get(key, 0)
        self.temp_data[key] = cur + 1
        return cur

    def note_dependency(self, filename: str) -> None:
        """Add *filename* as a dependency of the current document.

        This means that the document will be rebuilt if this file changes.

        *filename* should be absolute or relative to the source directory.
        """
        self.dependencies[self.docname].add(filename)

    def note_included(self, filename: str) -> None:
        """Add *filename* as a included from other document.

        This means the document is not orphaned.

        *filename* should be absolute or relative to the source directory.
        """
        self.included[self.docname].add(self.path2doc(filename))

    def note_reread(self) -> None:
        """Add the current document to the list of documents that will
        automatically be re-read at the next build.
        """
        self.reread_always.add(self.docname)

    def get_domain(self, domainname: str) -> Domain:
        """Return the domain instance with the specified name.

        Raises an ExtensionError if the domain is not registered.
        """
        try:
            return self.domains[domainname]
        except KeyError:
            raise ExtensionError(__('Domain %r is not registered') % domainname)

    # --------- RESOLVING REFERENCES AND TOCTREES ------------------------------

    def get_doctree(self, docname: str) -> nodes.document:
        """Read the doctree for a file from the pickle and return it."""
        filename = path.join(self.doctreedir, docname + '.doctree')
        with open(filename, 'rb') as f:
            doctree = pickle.load(f)
        doctree.settings.env = self
        doctree.reporter = LoggingReporter(self.doc2path(docname))
        return doctree

    def get_and_resolve_doctree(self, docname: str, builder: "Builder",
                                doctree: nodes.document = None, prune_toctrees: bool = True,
                                includehidden: bool = False) -> nodes.document:
        """Read the doctree from the pickle, resolve cross-references and
        toctrees and return it.
        """
        if doctree is None:
            doctree = self.get_doctree(docname)

        # resolve all pending cross-references
        self.apply_post_transforms(doctree, docname)

        # now, resolve all toctree nodes
        for toctreenode in doctree.traverse(addnodes.toctree):
            result = TocTree(self).resolve(docname, builder, toctreenode,
                                           prune=prune_toctrees,
                                           includehidden=includehidden)
            if result is None:
                toctreenode.replace_self([])
            else:
                toctreenode.replace_self(result)

        return doctree

    def resolve_toctree(self, docname: str, builder: "Builder", toctree: addnodes.toctree,
                        prune: bool = True, maxdepth: int = 0, titles_only: bool = False,
                        collapse: bool = False, includehidden: bool = False) -> Node:
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
        return TocTree(self).resolve(docname, builder, toctree, prune,
                                     maxdepth, titles_only, collapse,
                                     includehidden)

    def resolve_references(self, doctree: nodes.document, fromdocname: str,
                           builder: "Builder") -> None:
        self.apply_post_transforms(doctree, fromdocname)

    def apply_post_transforms(self, doctree: nodes.document, docname: str) -> None:
        """Apply all post-transforms."""
        try:
            # set env.docname during applying post-transforms
            backup = copy(self.temp_data)
            self.temp_data['docname'] = docname

            transformer = SphinxTransformer(doctree)
            transformer.set_environment(self)
            transformer.add_transforms(self.app.registry.get_post_transforms())
            transformer.apply_transforms()
        finally:
            self.temp_data = backup

        # allow custom references to be resolved
        self.events.emit('doctree-resolved', doctree, docname)

    def collect_relations(self) -> Dict[str, List[str]]:
        traversed = set()

        def traverse_toctree(parent: str, docname: str) -> Iterator[Tuple[str, str]]:
            if parent == docname:
                logger.warning(__('self referenced toctree found. Ignored.'), location=docname)
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

    def check_consistency(self) -> None:
        """Do consistency checks."""
        included = set().union(*self.included.values())  # type: ignore
        for docname in sorted(self.all_docs):
            if docname not in self.files_to_rebuild:
                if docname == self.config.master_doc:
                    # the master file is not included anywhere ;)
                    continue
                if docname in included:
                    # the document is included from other documents
                    continue
                if 'orphan' in self.metadata[docname]:
                    continue
                logger.warning(__('document isn\'t included in any toctree'),
                               location=docname)

        # call check-consistency for all extensions
        for domain in self.domains.values():
            domain.check_consistency()
        self.events.emit('env-check-consistency', self)

    # --------- METHODS FOR COMPATIBILITY --------------------------------------

    def update(self, config: Config, srcdir: str, doctreedir: str) -> List[str]:
        warnings.warn('env.update() is deprecated. Please use builder.read() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.app.builder.read()

    def _read_serial(self, docnames: List[str], app: "Sphinx") -> None:
        warnings.warn('env._read_serial() is deprecated. Please use builder.read() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.app.builder._read_serial(docnames)

    def _read_parallel(self, docnames: List[str], app: "Sphinx", nproc: int) -> None:
        warnings.warn('env._read_parallel() is deprecated. Please use builder.read() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.app.builder._read_parallel(docnames, nproc)

    def read_doc(self, docname: str, app: "Sphinx" = None) -> None:
        warnings.warn('env.read_doc() is deprecated. Please use builder.read_doc() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        self.app.builder.read_doc(docname)

    def write_doctree(self, docname: str, doctree: nodes.document) -> None:
        warnings.warn('env.write_doctree() is deprecated. '
                      'Please use builder.write_doctree() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        self.app.builder.write_doctree(docname, doctree)

    @property
    def _nitpick_ignore(self) -> List[str]:
        warnings.warn('env._nitpick_ignore is deprecated. '
                      'Please use config.nitpick_ignore instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.config.nitpick_ignore

    @staticmethod
    def load(f: IO, app: "Sphinx" = None) -> "BuildEnvironment":
        warnings.warn('BuildEnvironment.load() is deprecated. '
                      'Please use pickle.load() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        try:
            env = pickle.load(f)
        except Exception as exc:
            # This can happen for example when the pickle is from a
            # different version of Sphinx.
            raise OSError(exc)
        if app:
            env.app = app
            env.config.values = app.config.values
        return env

    @classmethod
    def loads(cls, string: bytes, app: "Sphinx" = None) -> "BuildEnvironment":
        warnings.warn('BuildEnvironment.loads() is deprecated. '
                      'Please use pickle.loads() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        io = BytesIO(string)
        return cls.load(io, app)

    @classmethod
    def frompickle(cls, filename: str, app: "Sphinx") -> "BuildEnvironment":
        warnings.warn('BuildEnvironment.frompickle() is deprecated. '
                      'Please use pickle.load() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        with open(filename, 'rb') as f:
            return cls.load(f, app)

    @staticmethod
    def dump(env: "BuildEnvironment", f: IO) -> None:
        warnings.warn('BuildEnvironment.dump() is deprecated. '
                      'Please use pickle.dump() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        pickle.dump(env, f, pickle.HIGHEST_PROTOCOL)

    @classmethod
    def dumps(cls, env: "BuildEnvironment") -> bytes:
        warnings.warn('BuildEnvironment.dumps() is deprecated. '
                      'Please use pickle.dumps() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        io = BytesIO()
        cls.dump(env, io)
        return io.getvalue()

    def topickle(self, filename: str) -> None:
        warnings.warn('env.topickle() is deprecated. '
                      'Please use pickle.dump() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        with open(filename, 'wb') as f:
            self.dump(self, f)

    @property
    def versionchanges(self) -> Dict[str, List[Tuple[str, str, int, str, str, str]]]:
        warnings.warn('env.versionchanges() is deprecated. '
                      'Please use ChangeSetDomain instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return self.domaindata['changeset']['changes']

    def note_versionchange(self, type: str, version: str,
                           node: addnodes.versionmodified, lineno: int) -> None:
        warnings.warn('env.note_versionchange() is deprecated. '
                      'Please use ChangeSetDomain.note_changeset() instead.',
                      RemovedInSphinx30Warning, stacklevel=2)
        node['type'] = type
        node['version'] = version
        node.line = lineno
        self.get_domain('changeset').note_changeset(node)  # type: ignore


from sphinx.errors import NoUri  # NOQA


deprecated_alias('sphinx.environment',
                 {
                     'NoUri': NoUri,
                 },
                 RemovedInSphinx30Warning)
