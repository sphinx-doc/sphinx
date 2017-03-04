# -*- coding: utf-8 -*-
"""
    sphinx.application
    ~~~~~~~~~~~~~~~~~~

    Sphinx application object.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import sys
import types
import warnings
import posixpath
import traceback
from os import path
from collections import deque

from six import iteritems, itervalues
from six.moves import cStringIO

from docutils import nodes
from docutils.parsers.rst import convert_directive_function, \
    directives, roles

import sphinx
from sphinx import package_dir, locale
from sphinx.config import Config
from sphinx.errors import SphinxError, ExtensionError, VersionRequirementError, \
    ConfigError
from sphinx.domains import ObjType
from sphinx.domains.std import GenericObject, Target, StandardDomain
from sphinx.deprecation import RemovedInSphinx17Warning, RemovedInSphinx20Warning
from sphinx.environment import BuildEnvironment
from sphinx.io import SphinxStandaloneReader
from sphinx.roles import XRefRole
from sphinx.util import pycompat  # noqa: F401
from sphinx.util import import_object
from sphinx.util import logging
from sphinx.util import status_iterator, old_status_iterator, display_chunk
from sphinx.util.tags import Tags
from sphinx.util.osutil import ENOENT
from sphinx.util.console import bold, darkgreen  # type: ignore
from sphinx.util.docutils import is_html5_writer_available
from sphinx.util.i18n import find_catalog_source_files

if False:
    # For type annotation
    from typing import Any, Callable, Dict, IO, Iterable, Iterator, List, Tuple, Type, Union  # NOQA
    from docutils.parsers import Parser  # NOQA
    from docutils.transform import Transform  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.domains import Domain, Index  # NOQA
    from sphinx.environment.collectors import EnvironmentCollector  # NOQA

# List of all known core events. Maps name to arguments description.
events = {
    'builder-inited': '',
    'env-get-outdated': 'env, added, changed, removed',
    'env-get-updated': 'env',
    'env-purge-doc': 'env, docname',
    'env-before-read-docs': 'env, docnames',
    'source-read': 'docname, source text',
    'doctree-read': 'the doctree before being pickled',
    'env-merge-info': 'env, read docnames, other env instance',
    'missing-reference': 'env, node, contnode',
    'doctree-resolved': 'doctree, docname',
    'env-updated': 'env',
    'html-collect-pages': 'builder',
    'html-page-context': 'pagename, context, doctree or None',
    'build-finished': 'exception',
}  # type: Dict[unicode, unicode]
builtin_extensions = (
    'sphinx.builders.applehelp',
    'sphinx.builders.changes',
    'sphinx.builders.epub',
    'sphinx.builders.epub3',
    'sphinx.builders.devhelp',
    'sphinx.builders.dummy',
    'sphinx.builders.gettext',
    'sphinx.builders.html',
    'sphinx.builders.htmlhelp',
    'sphinx.builders.latex',
    'sphinx.builders.linkcheck',
    'sphinx.builders.manpage',
    'sphinx.builders.qthelp',
    'sphinx.builders.texinfo',
    'sphinx.builders.text',
    'sphinx.builders.websupport',
    'sphinx.builders.xml',
    'sphinx.domains.c',
    'sphinx.domains.cpp',
    'sphinx.domains.javascript',
    'sphinx.domains.python',
    'sphinx.domains.rst',
    'sphinx.domains.std',
    'sphinx.directives',
    'sphinx.directives.code',
    'sphinx.directives.other',
    'sphinx.directives.patches',
    'sphinx.roles',
    # collectors should be loaded by specific order
    'sphinx.environment.collectors.dependencies',
    'sphinx.environment.collectors.asset',
    'sphinx.environment.collectors.metadata',
    'sphinx.environment.collectors.title',
    'sphinx.environment.collectors.toctree',
    'sphinx.environment.collectors.indexentries',
)  # type: Tuple[unicode, ...]

CONFIG_FILENAME = 'conf.py'
ENV_PICKLE_FILENAME = 'environment.pickle'

# list of deprecated extensions. Keys are extension name.
# Values are Sphinx version that merge the extension.
EXTENSION_BLACKLIST = {"sphinxjp.themecore": "1.2"}  # type: Dict[unicode, unicode]

logger = logging.getLogger(__name__)


class Sphinx(object):

    def __init__(self, srcdir, confdir, outdir, doctreedir, buildername,
                 confoverrides=None, status=sys.stdout, warning=sys.stderr,
                 freshenv=False, warningiserror=False, tags=None, verbosity=0,
                 parallel=0):
        # type: (unicode, unicode, unicode, unicode, unicode, Dict, IO, IO, bool, bool, List[unicode], int, int) -> None  # NOQA
        self.verbosity = verbosity
        self.next_listener_id = 0
        self._extensions = {}                   # type: Dict[unicode, Any]
        self._extension_metadata = {}           # type: Dict[unicode, Dict[unicode, Any]]
        self._additional_source_parsers = {}    # type: Dict[unicode, Parser]
        self._listeners = {}                    # type: Dict[unicode, Dict[int, Callable]]
        self._setting_up_extension = ['?']      # type: List[unicode]
        self.domains = {}                       # type: Dict[unicode, Type[Domain]]
        self.buildername = buildername
        self.builderclasses = {}                # type: Dict[unicode, Type[Builder]]
        self.builder = None                     # type: Builder
        self.env = None                         # type: BuildEnvironment
        self.enumerable_nodes = {}              # type: Dict[nodes.Node, Tuple[unicode, Callable]]  # NOQA

        self.srcdir = srcdir
        self.confdir = confdir
        self.outdir = outdir
        self.doctreedir = doctreedir

        self.parallel = parallel

        if status is None:
            self._status = cStringIO()      # type: IO
            self.quiet = True
        else:
            self._status = status
            self.quiet = False

        if warning is None:
            self._warning = cStringIO()     # type: IO
        else:
            self._warning = warning
        self._warncount = 0
        self.warningiserror = warningiserror
        logging.setup(self, self._status, self._warning)

        self._events = events.copy()
        self._translators = {}              # type: Dict[unicode, nodes.GenericNodeVisitor]

        # keep last few messages for traceback
        self.messagelog = deque(maxlen=10)  # type: deque

        # say hello to the world
        logger.info(bold('Running Sphinx v%s' % sphinx.__display_version__))

        # status code for command-line application
        self.statuscode = 0

        if not path.isdir(outdir):
            logger.info('making output directory...')
            os.makedirs(outdir)

        # read config
        self.tags = Tags(tags)
        self.config = Config(confdir, CONFIG_FILENAME,
                             confoverrides or {}, self.tags)
        self.config.check_unicode()
        # defer checking types until i18n has been initialized

        # initialize some limited config variables before loading extensions
        self.config.pre_init_values()

        # check the Sphinx version if requested
        if self.config.needs_sphinx and self.config.needs_sphinx > sphinx.__display_version__:
            raise VersionRequirementError(
                'This project needs at least Sphinx v%s and therefore cannot '
                'be built with this version.' % self.config.needs_sphinx)

        # set confdir to srcdir if -C given (!= no confdir); a few pieces
        # of code expect a confdir to be set
        if self.confdir is None:
            self.confdir = self.srcdir

        # load all built-in extension modules
        for extension in builtin_extensions:
            self.setup_extension(extension)

        # extension loading support for alabaster theme
        # self.config.html_theme is not set from conf.py at here
        # for now, sphinx always load a 'alabaster' extension.
        if 'alabaster' not in self.config.extensions:
            self.config.extensions.append('alabaster')

        # load all user-given extension modules
        for extension in self.config.extensions:
            self.setup_extension(extension)
        # the config file itself can be an extension
        if self.config.setup:
            self._setting_up_extension = ['conf.py']
            # py31 doesn't have 'callable' function for below check
            if hasattr(self.config.setup, '__call__'):
                self.config.setup(self)
            else:
                raise ConfigError(
                    "'setup' that is specified in the conf.py has not been " +
                    "callable. Please provide a callable `setup` function " +
                    "in order to behave as a sphinx extension conf.py itself."
                )

        # now that we know all config values, collect them from conf.py
        self.config.init_values()

        # check extension versions if requested
        if self.config.needs_extensions:
            for extname, needs_ver in self.config.needs_extensions.items():
                if extname not in self._extensions:
                    logger.warning('needs_extensions config value specifies a '
                                   'version requirement for extension %s, but it is '
                                   'not loaded', extname)
                    continue
                has_ver = self._extension_metadata[extname]['version']
                if has_ver == 'unknown version' or needs_ver > has_ver:
                    raise VersionRequirementError(
                        'This project needs the extension %s at least in '
                        'version %s and therefore cannot be built with the '
                        'loaded version (%s).' % (extname, needs_ver, has_ver))

        # check primary_domain if requested
        if self.config.primary_domain and self.config.primary_domain not in self.domains:
            logger.warning('primary_domain %r not found, ignored.', self.config.primary_domain)

        # set up translation infrastructure
        self._init_i18n()
        # check all configuration values for permissible types
        self.config.check_types()
        # set up source_parsers
        self._init_source_parsers()
        # set up the build environment
        self._init_env(freshenv)
        # set up the builder
        self._init_builder(self.buildername)
        # set up the enumerable nodes
        self._init_enumerable_nodes()

    def _init_i18n(self):
        # type: () -> None
        """Load translated strings from the configured localedirs if enabled in
        the configuration.
        """
        if self.config.language is not None:
            logger.info(bold('loading translations [%s]... ' % self.config.language),
                        nonl=True)
            user_locale_dirs = [
                path.join(self.srcdir, x) for x in self.config.locale_dirs]
            # compile mo files if sphinx.po file in user locale directories are updated
            for catinfo in find_catalog_source_files(
                    user_locale_dirs, self.config.language, domains=['sphinx'],
                    charset=self.config.source_encoding):
                catinfo.write_mo(self.config.language)
            locale_dirs = [None, path.join(package_dir, 'locale')] + user_locale_dirs
        else:
            locale_dirs = []
        self.translator, has_translation = locale.init(locale_dirs, self.config.language)
        if self.config.language is not None:
            if has_translation or self.config.language == 'en':
                # "en" never needs to be translated
                logger.info('done')
            else:
                logger.info('not available for built-in messages')

    def _init_source_parsers(self):
        # type: () -> None
        for suffix, parser in iteritems(self._additional_source_parsers):
            if suffix not in self.config.source_suffix:
                self.config.source_suffix.append(suffix)
            if suffix not in self.config.source_parsers:
                self.config.source_parsers[suffix] = parser

    def _init_env(self, freshenv):
        # type: (bool) -> None
        if freshenv:
            self.env = BuildEnvironment(self.srcdir, self.doctreedir, self.config)
            self.env.find_files(self.config, self.buildername)
            for domain in self.domains.keys():
                self.env.domains[domain] = self.domains[domain](self.env)
        else:
            try:
                logger.info(bold('loading pickled environment... '), nonl=True)
                self.env = BuildEnvironment.frompickle(
                    self.srcdir, self.config, path.join(self.doctreedir, ENV_PICKLE_FILENAME))
                self.env.domains = {}
                for domain in self.domains.keys():
                    # this can raise if the data version doesn't fit
                    self.env.domains[domain] = self.domains[domain](self.env)
                logger.info('done')
            except Exception as err:
                if isinstance(err, IOError) and err.errno == ENOENT:
                    logger.info('not yet created')
                else:
                    logger.info('failed: %s', err)
                self._init_env(freshenv=True)

    def _init_builder(self, buildername):
        # type: (unicode) -> None
        if buildername is None:
            print('No builder selected, using default: html', file=self._status)
            buildername = 'html'
        if buildername not in self.builderclasses:
            raise SphinxError('Builder name %s not registered' % buildername)

        builderclass = self.builderclasses[buildername]
        self.builder = builderclass(self)
        self.emit('builder-inited')

    def _init_enumerable_nodes(self):
        # type: () -> None
        for node, settings in iteritems(self.enumerable_nodes):
            self.env.get_domain('std').enumerable_nodes[node] = settings  # type: ignore

    # ---- main "build" method -------------------------------------------------

    def build(self, force_all=False, filenames=None):
        # type: (bool, List[unicode]) -> None
        try:
            if force_all:
                self.builder.compile_all_catalogs()
                self.builder.build_all()
            elif filenames:
                self.builder.compile_specific_catalogs(filenames)
                self.builder.build_specific(filenames)
            else:
                self.builder.compile_update_catalogs()
                self.builder.build_update()

            status = (self.statuscode == 0 and
                      'succeeded' or 'finished with problems')
            if self._warncount:
                logger.info(bold('build %s, %s warning%s.' %
                                 (status, self._warncount,
                                  self._warncount != 1 and 's' or '')))
            else:
                logger.info(bold('build %s.' % status))
        except Exception as err:
            # delete the saved env to force a fresh build next time
            envfile = path.join(self.doctreedir, ENV_PICKLE_FILENAME)
            if path.isfile(envfile):
                os.unlink(envfile)
            self.emit('build-finished', err)
            raise
        else:
            self.emit('build-finished', None)
        self.builder.cleanup()

    # ---- logging handling ----------------------------------------------------
    def warn(self, message, location=None, prefix=None,
             type=None, subtype=None, colorfunc=None):
        # type: (unicode, unicode, unicode, unicode, unicode, Callable) -> None
        """Emit a warning.

        If *location* is given, it should either be a tuple of (docname, lineno)
        or a string describing the location of the warning as well as possible.

        *prefix* usually should not be changed.

        *type* and *subtype* are used to suppress warnings with :confval:`suppress_warnings`.

        .. note::

           For warnings emitted during parsing, you should use
           :meth:`.BuildEnvironment.warn` since that will collect all
           warnings during parsing for later output.
        """
        if prefix:
            warnings.warn('prefix option of warn() is now deprecated.',
                          RemovedInSphinx17Warning)
        if colorfunc:
            warnings.warn('colorfunc option of warn() is now deprecated.',
                          RemovedInSphinx17Warning)

        warnings.warn('app.warning() is now deprecated. Use sphinx.util.logging instead.',
                      RemovedInSphinx20Warning)
        logger.warning(message, type=type, subtype=subtype, location=location)

    def info(self, message='', nonl=False):
        # type: (unicode, bool) -> None
        """Emit an informational message.

        If *nonl* is true, don't emit a newline at the end (which implies that
        more info output will follow soon.)
        """
        warnings.warn('app.info() is now deprecated. Use sphinx.util.logging instead.',
                      RemovedInSphinx20Warning)
        logger.info(message, nonl=nonl)

    def verbose(self, message, *args, **kwargs):
        # type: (unicode, Any, Any) -> None
        """Emit a verbose informational message."""
        warnings.warn('app.verbose() is now deprecated. Use sphinx.util.logging instead.',
                      RemovedInSphinx20Warning)
        logger.verbose(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        # type: (unicode, Any, Any) -> None
        """Emit a debug-level informational message."""
        warnings.warn('app.debug() is now deprecated. Use sphinx.util.logging instead.',
                      RemovedInSphinx20Warning)
        logger.debug(message, *args, **kwargs)

    def debug2(self, message, *args, **kwargs):
        # type: (unicode, Any, Any) -> None
        """Emit a lowlevel debug-level informational message."""
        warnings.warn('app.debug2() is now deprecated. Use debug() instead.',
                      RemovedInSphinx20Warning)
        logger.debug(message, *args, **kwargs)

    def _display_chunk(chunk):
        # type: (Any) -> unicode
        warnings.warn('app._display_chunk() is now deprecated. '
                      'Use sphinx.util.display_chunk() instead.',
                      RemovedInSphinx17Warning)
        return display_chunk(chunk)

    def old_status_iterator(self, iterable, summary, colorfunc=darkgreen,
                            stringify_func=display_chunk):
        # type: (Iterable, unicode, Callable, Callable[[Any], unicode]) -> Iterator
        warnings.warn('app.old_status_iterator() is now deprecated. '
                      'Use sphinx.util.status_iterator() instead.',
                      RemovedInSphinx17Warning)
        for item in old_status_iterator(iterable, summary,
                                        color="darkgreen", stringify_func=stringify_func):
            yield item

    # new version with progress info
    def status_iterator(self, iterable, summary, colorfunc=darkgreen, length=0,
                        stringify_func=_display_chunk):
        # type: (Iterable, unicode, Callable, int, Callable[[Any], unicode]) -> Iterable
        warnings.warn('app.status_iterator() is now deprecated. '
                      'Use sphinx.util.status_iterator() instead.',
                      RemovedInSphinx17Warning)
        for item in status_iterator(iterable, summary, length=length, verbosity=self.verbosity,
                                    color="darkgreen", stringify_func=stringify_func):
            yield item

    # ---- general extensibility interface -------------------------------------

    def setup_extension(self, extension):
        # type: (unicode) -> None
        """Import and setup a Sphinx extension module. No-op if called twice."""
        logger.debug('[app] setting up extension: %r', extension)
        if extension in self._extensions:
            return
        if extension in EXTENSION_BLACKLIST:
            logger.warning('the extension %r was already merged with Sphinx since version %s; '
                           'this extension is ignored.',
                           extension, EXTENSION_BLACKLIST[extension])
            return
        self._setting_up_extension.append(extension)
        try:
            mod = __import__(extension, None, None, ['setup'])
        except ImportError as err:
            logger.verbose('Original exception:\n' + traceback.format_exc())
            raise ExtensionError('Could not import extension %s' % extension,
                                 err)
        if not hasattr(mod, 'setup'):
            logger.warning('extension %r has no setup() function; is it really '
                           'a Sphinx extension module?', extension)
            ext_meta = None
        else:
            try:
                ext_meta = mod.setup(self)
            except VersionRequirementError as err:
                # add the extension name to the version required
                raise VersionRequirementError(
                    'The %s extension used by this project needs at least '
                    'Sphinx v%s; it therefore cannot be built with this '
                    'version.' % (extension, err))
        if ext_meta is None:
            ext_meta = {}
            # special-case for compatibility
            if extension == 'rst2pdf.pdfbuilder':
                ext_meta = {'parallel_read_safe': True}
        try:
            if not ext_meta.get('version'):
                ext_meta['version'] = 'unknown version'
        except Exception:
            logger.warning('extension %r returned an unsupported object from '
                           'its setup() function; it should return None or a '
                           'metadata dictionary', extension)
            ext_meta = {'version': 'unknown version'}
        self._extensions[extension] = mod
        self._extension_metadata[extension] = ext_meta
        self._setting_up_extension.pop()

    def require_sphinx(self, version):
        # type: (unicode) -> None
        # check the Sphinx version if requested
        if version > sphinx.__display_version__[:3]:
            raise VersionRequirementError(version)

    def import_object(self, objname, source=None):
        # type: (str, unicode) -> Any
        """Import an object from a 'module.name' string."""
        return import_object(objname, source=None)

    # event interface

    def _validate_event(self, event):
        # type: (unicode) -> None
        if event not in self._events:
            raise ExtensionError('Unknown event name: %s' % event)

    def connect(self, event, callback):
        # type: (unicode, Callable) -> int
        self._validate_event(event)
        listener_id = self.next_listener_id
        if event not in self._listeners:
            self._listeners[event] = {listener_id: callback}
        else:
            self._listeners[event][listener_id] = callback
        self.next_listener_id += 1
        logger.debug('[app] connecting event %r: %r [id=%s]',
                     event, callback, listener_id)
        return listener_id

    def disconnect(self, listener_id):
        # type: (int) -> None
        logger.debug('[app] disconnecting event: [id=%s]', listener_id)
        for event in itervalues(self._listeners):
            event.pop(listener_id, None)

    def emit(self, event, *args):
        # type: (unicode, Any) -> List
        try:
            logger.debug('[app] emitting event: %r%s', event, repr(args)[:100])
        except Exception:
            # not every object likes to be repr()'d (think
            # random stuff coming via autodoc)
            pass
        results = []
        if event in self._listeners:
            for _, callback in iteritems(self._listeners[event]):
                results.append(callback(self, *args))
        return results

    def emit_firstresult(self, event, *args):
        # type: (unicode, Any) -> Any
        for result in self.emit(event, *args):
            if result is not None:
                return result
        return None

    # registering addon parts

    def add_builder(self, builder):
        # type: (Type[Builder]) -> None
        logger.debug('[app] adding builder: %r', builder)
        if not hasattr(builder, 'name'):
            raise ExtensionError('Builder class %s has no "name" attribute'
                                 % builder)
        if builder.name in self.builderclasses:
            raise ExtensionError(
                'Builder %r already exists (in module %s)' % (
                    builder.name, self.builderclasses[builder.name].__module__))
        self.builderclasses[builder.name] = builder

    def add_config_value(self, name, default, rebuild, types=()):
        # type: (unicode, Any, Union[bool, unicode], Any) -> None
        logger.debug('[app] adding config value: %r',
                     (name, default, rebuild) + ((types,) if types else ()))  # type: ignore
        if name in self.config:
            raise ExtensionError('Config value %r already present' % name)
        if rebuild in (False, True):
            rebuild = rebuild and 'env' or ''
        self.config.add(name, default, rebuild, types)

    def add_event(self, name):
        # type: (unicode) -> None
        logger.debug('[app] adding event: %r', name)
        if name in self._events:
            raise ExtensionError('Event %r already present' % name)
        self._events[name] = ''

    def set_translator(self, name, translator_class):
        # type: (unicode, Any) -> None
        logger.info(bold('A Translator for the %s builder is changed.' % name))
        self._translators[name] = translator_class

    def add_node(self, node, **kwds):
        # type: (nodes.Node, Any) -> None
        logger.debug('[app] adding node: %r', (node, kwds))
        if not kwds.pop('override', False) and \
           hasattr(nodes.GenericNodeVisitor, 'visit_' + node.__name__):
            logger.warning('while setting up extension %s: node class %r is '
                           'already registered, its visitors will be overridden',
                           self._setting_up_extension, node.__name__,
                           type='app', subtype='add_node')
        nodes._add_node_class_names([node.__name__])
        for key, val in iteritems(kwds):
            try:
                visit, depart = val
            except ValueError:
                raise ExtensionError('Value for key %r must be a '
                                     '(visit, depart) function tuple' % key)
            translator = self._translators.get(key)
            translators = []
            if translator is not None:
                translators.append(translator)
            elif key == 'html':
                from sphinx.writers.html import HTMLTranslator
                translators.append(HTMLTranslator)
                if is_html5_writer_available():
                    from sphinx.writers.html5 import HTML5Translator
                    translators.append(HTML5Translator)
            elif key == 'latex':
                from sphinx.writers.latex import LaTeXTranslator
                translators.append(LaTeXTranslator)
            elif key == 'text':
                from sphinx.writers.text import TextTranslator
                translators.append(TextTranslator)
            elif key == 'man':
                from sphinx.writers.manpage import ManualPageTranslator
                translators.append(ManualPageTranslator)
            elif key == 'texinfo':
                from sphinx.writers.texinfo import TexinfoTranslator
                translators.append(TexinfoTranslator)

            for translator in translators:
                setattr(translator, 'visit_' + node.__name__, visit)
                if depart:
                    setattr(translator, 'depart_' + node.__name__, depart)

    def add_enumerable_node(self, node, figtype, title_getter=None, **kwds):
        # type: (nodes.Node, unicode, Callable, Any) -> None
        self.enumerable_nodes[node] = (figtype, title_getter)
        self.add_node(node, **kwds)

    def _directive_helper(self, obj, content=None, arguments=None, **options):
        # type: (Any, unicode, Any, Any) -> Any
        if isinstance(obj, (types.FunctionType, types.MethodType)):
            obj.content = content                       # type: ignore
            obj.arguments = arguments or (0, 0, False)  # type: ignore
            obj.options = options                       # type: ignore
            return convert_directive_function(obj)
        else:
            if content or arguments or options:
                raise ExtensionError('when adding directive classes, no '
                                     'additional arguments may be given')
            return obj

    def add_directive(self, name, obj, content=None, arguments=None, **options):
        # type: (unicode, Any, unicode, Any, Any) -> None
        logger.debug('[app] adding directive: %r',
                     (name, obj, content, arguments, options))
        if name in directives._directives:
            logger.warning('while setting up extension %s: directive %r is '
                           'already registered, it will be overridden',
                           self._setting_up_extension[-1], name,
                           type='app', subtype='add_directive')
        directives.register_directive(
            name, self._directive_helper(obj, content, arguments, **options))

    def add_role(self, name, role):
        # type: (unicode, Any) -> None
        logger.debug('[app] adding role: %r', (name, role))
        if name in roles._roles:
            logger.warning('while setting up extension %s: role %r is '
                           'already registered, it will be overridden',
                           self._setting_up_extension[-1], name,
                           type='app', subtype='add_role')
        roles.register_local_role(name, role)

    def add_generic_role(self, name, nodeclass):
        # type: (unicode, Any) -> None
        # don't use roles.register_generic_role because it uses
        # register_canonical_role
        logger.debug('[app] adding generic role: %r', (name, nodeclass))
        if name in roles._roles:
            logger.warning('while setting up extension %s: role %r is '
                           'already registered, it will be overridden',
                           self._setting_up_extension[-1], name,
                           type='app', subtype='add_generic_role')
        role = roles.GenericRole(name, nodeclass)
        roles.register_local_role(name, role)

    def add_domain(self, domain):
        # type: (Type[Domain]) -> None
        logger.debug('[app] adding domain: %r', domain)
        if domain.name in self.domains:
            raise ExtensionError('domain %s already registered' % domain.name)
        self.domains[domain.name] = domain

    def override_domain(self, domain):
        # type: (Type[Domain]) -> None
        logger.debug('[app] overriding domain: %r', domain)
        if domain.name not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain.name)
        if not issubclass(domain, self.domains[domain.name]):
            raise ExtensionError('new domain not a subclass of registered %s '
                                 'domain' % domain.name)
        self.domains[domain.name] = domain

    def add_directive_to_domain(self, domain, name, obj,
                                content=None, arguments=None, **options):
        # type: (unicode, unicode, Any, unicode, Any, Any) -> None
        logger.debug('[app] adding directive to domain: %r',
                     (domain, name, obj, content, arguments, options))
        if domain not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain)
        self.domains[domain].directives[name] = \
            self._directive_helper(obj, content, arguments, **options)

    def add_role_to_domain(self, domain, name, role):
        # type: (unicode, unicode, Any) -> None
        logger.debug('[app] adding role to domain: %r', (domain, name, role))
        if domain not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain)
        self.domains[domain].roles[name] = role

    def add_index_to_domain(self, domain, index):
        # type: (unicode, Type[Index]) -> None
        logger.debug('[app] adding index to domain: %r', (domain, index))
        if domain not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain)
        self.domains[domain].indices.append(index)

    def add_object_type(self, directivename, rolename, indextemplate='',
                        parse_node=None, ref_nodeclass=None, objname='',
                        doc_field_types=[]):
        # type: (unicode, unicode, unicode, Callable, nodes.Node, unicode, List) -> None
        logger.debug('[app] adding object type: %r',
                     (directivename, rolename, indextemplate, parse_node,
                      ref_nodeclass, objname, doc_field_types))
        StandardDomain.object_types[directivename] = \
            ObjType(objname or directivename, rolename)
        # create a subclass of GenericObject as the new directive
        new_directive = type(directivename, (GenericObject, object),  # type: ignore
                             {'indextemplate': indextemplate,
                              'parse_node': staticmethod(parse_node),  # type: ignore
                              'doc_field_types': doc_field_types})
        StandardDomain.directives[directivename] = new_directive
        # XXX support more options?
        StandardDomain.roles[rolename] = XRefRole(innernodeclass=ref_nodeclass)

    # backwards compatible alias
    add_description_unit = add_object_type

    def add_crossref_type(self, directivename, rolename, indextemplate='',
                          ref_nodeclass=None, objname=''):
        # type: (unicode, unicode, unicode, nodes.Node, unicode) -> None
        logger.debug('[app] adding crossref type: %r',
                     (directivename, rolename, indextemplate, ref_nodeclass,
                      objname))
        StandardDomain.object_types[directivename] = \
            ObjType(objname or directivename, rolename)
        # create a subclass of Target as the new directive
        new_directive = type(directivename, (Target, object),  # type: ignore
                             {'indextemplate': indextemplate})
        StandardDomain.directives[directivename] = new_directive
        # XXX support more options?
        StandardDomain.roles[rolename] = XRefRole(innernodeclass=ref_nodeclass)

    def add_transform(self, transform):
        # type: (Transform) -> None
        logger.debug('[app] adding transform: %r', transform)
        SphinxStandaloneReader.transforms.append(transform)

    def add_javascript(self, filename):
        # type: (unicode) -> None
        logger.debug('[app] adding javascript: %r', filename)
        from sphinx.builders.html import StandaloneHTMLBuilder
        if '://' in filename:
            StandaloneHTMLBuilder.script_files.append(filename)
        else:
            StandaloneHTMLBuilder.script_files.append(
                posixpath.join('_static', filename))

    def add_stylesheet(self, filename, alternate=None, title=None):
        # type: (unicode, unicode, unicode) -> None
        logger.debug('[app] adding stylesheet: %r', filename)
        from sphinx.builders.html import StandaloneHTMLBuilder
        props = {} # type: Dict[unicode, Union[unicode, bool]]
        if alternate is not None:
            props['alternate'] = bool(alternate)
        if title is not None:
            props['title'] = title
        if '://' in filename:
            fname = filename
        else:
            fname = posixpath.join('_static', filename)
        StandaloneHTMLBuilder.css_files.append(fname)
        StandaloneHTMLBuilder.css_props[fname] = props

    def add_latex_package(self, packagename, options=None):
        # type: (unicode, unicode) -> None
        logger.debug('[app] adding latex package: %r', packagename)
        if hasattr(self.builder, 'usepackages'):  # only for LaTeX builder
            self.builder.usepackages.append((packagename, options))  # type: ignore

    def add_lexer(self, alias, lexer):
        # type: (unicode, Any) -> None
        logger.debug('[app] adding lexer: %r', (alias, lexer))
        from sphinx.highlighting import lexers
        if lexers is None:
            return
        lexers[alias] = lexer

    def add_autodocumenter(self, cls):
        # type: (Any) -> None
        logger.debug('[app] adding autodocumenter: %r', cls)
        from sphinx.ext import autodoc
        autodoc.add_documenter(cls)
        self.add_directive('auto' + cls.objtype, autodoc.AutoDirective)

    def add_autodoc_attrgetter(self, type, getter):
        # type: (Any, Callable) -> None
        logger.debug('[app] adding autodoc attrgetter: %r', (type, getter))
        from sphinx.ext import autodoc
        autodoc.AutoDirective._special_attrgetters[type] = getter

    def add_search_language(self, cls):
        # type: (Any) -> None
        logger.debug('[app] adding search language: %r', cls)
        from sphinx.search import languages, SearchLanguage
        assert issubclass(cls, SearchLanguage)
        languages[cls.lang] = cls

    def add_source_parser(self, suffix, parser):
        # type: (unicode, Parser) -> None
        logger.debug('[app] adding search source_parser: %r, %r', suffix, parser)
        if suffix in self._additional_source_parsers:
            logger.warning('while setting up extension %s: source_parser for %r is '
                           'already registered, it will be overridden',
                           self._setting_up_extension[-1], suffix,
                           type='app', subtype='add_source_parser')
        self._additional_source_parsers[suffix] = parser

    def add_env_collector(self, collector):
        # type: (Type[EnvironmentCollector]) -> None
        logger.debug('[app] adding environment collector: %r', collector)
        collector().enable(self)


class TemplateBridge(object):
    """
    This class defines the interface for a "template bridge", that is, a class
    that renders templates given a template name and a context.
    """

    def init(self, builder, theme=None, dirs=None):
        # type: (Builder, unicode, List[unicode]) -> None
        """Called by the builder to initialize the template system.

        *builder* is the builder object; you'll probably want to look at the
        value of ``builder.config.templates_path``.

        *theme* is a :class:`sphinx.theming.Theme` object or None; in the latter
        case, *dirs* can be list of fixed directories to look for templates.
        """
        raise NotImplementedError('must be implemented in subclasses')

    def newest_template_mtime(self):
        # type: () -> float
        """Called by the builder to determine if output files are outdated
        because of template changes.  Return the mtime of the newest template
        file that was changed.  The default implementation returns ``0``.
        """
        return 0

    def render(self, template, context):
        # type: (unicode, Dict) -> None
        """Called by the builder to render a template given as a filename with
        a specified context (a Python dictionary).
        """
        raise NotImplementedError('must be implemented in subclasses')

    def render_string(self, template, context):
        # type: (unicode, Dict) -> unicode
        """Called by the builder to render a template given as a string with a
        specified context (a Python dictionary).
        """
        raise NotImplementedError('must be implemented in subclasses')
