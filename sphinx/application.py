# -*- coding: utf-8 -*-
"""
    sphinx.application
    ~~~~~~~~~~~~~~~~~~

    Sphinx application object.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import types
import posixpath
from os import path
from cStringIO import StringIO

from docutils import nodes
from docutils.parsers.rst import convert_directive_function, \
     directives, roles

import sphinx
from sphinx import package_dir, locale
from sphinx.roles import XRefRole
from sphinx.config import Config
from sphinx.errors import SphinxError, SphinxWarning, ExtensionError, \
     VersionRequirementError
from sphinx.domains import ObjType, BUILTIN_DOMAINS
from sphinx.domains.std import GenericObject, Target, StandardDomain
from sphinx.builders import BUILTIN_BUILDERS
from sphinx.environment import BuildEnvironment, SphinxStandaloneReader
from sphinx.util import pycompat  # imported for side-effects
from sphinx.util.tags import Tags
from sphinx.util.osutil import ENOENT
from sphinx.util.console import bold


# Directive is either new-style or old-style
clstypes = (type, types.ClassType)

# List of all known core events. Maps name to arguments description.
events = {
    'builder-inited': '',
    'env-purge-doc': 'env, docname',
    'source-read': 'docname, source text',
    'doctree-read': 'the doctree before being pickled',
    'missing-reference': 'env, node, contnode',
    'doctree-resolved': 'doctree, docname',
    'env-updated': 'env',
    'html-collect-pages': 'builder',
    'html-page-context': 'pagename, context, doctree or None',
    'build-finished': 'exception',
}

CONFIG_FILENAME = 'conf.py'
ENV_PICKLE_FILENAME = 'environment.pickle'


class Sphinx(object):

    def __init__(self, srcdir, confdir, outdir, doctreedir, buildername,
                 confoverrides=None, status=sys.stdout, warning=sys.stderr,
                 freshenv=False, warningiserror=False, tags=None):
        self.next_listener_id = 0
        self._extensions = {}
        self._listeners = {}
        self.domains = BUILTIN_DOMAINS.copy()
        self.builderclasses = BUILTIN_BUILDERS.copy()
        self.builder = None
        self.env = None

        self.srcdir = srcdir
        self.confdir = confdir
        self.outdir = outdir
        self.doctreedir = doctreedir

        if status is None:
            self._status = StringIO()
            self.quiet = True
        else:
            self._status = status
            self.quiet = False

        if warning is None:
            self._warning = StringIO()
        else:
            self._warning = warning
        self._warncount = 0
        self.warningiserror = warningiserror

        self._events = events.copy()

        # say hello to the world
        self.info(bold('Running Sphinx v%s' % sphinx.__version__))

        # status code for command-line application
        self.statuscode = 0

        # read config
        self.tags = Tags(tags)
        self.config = Config(confdir, CONFIG_FILENAME,
                             confoverrides or {}, self.tags)
        self.config.check_unicode(self.warn)

        # set confdir to srcdir if -C given (!= no confdir); a few pieces
        # of code expect a confdir to be set
        if self.confdir is None:
            self.confdir = self.srcdir

        # backwards compatibility: activate old C markup
        self.setup_extension('sphinx.ext.oldcmarkup')
        # load all user-given extension modules
        for extension in self.config.extensions:
            self.setup_extension(extension)
        # the config file itself can be an extension
        if self.config.setup:
            self.config.setup(self)

        # now that we know all config values, collect them from conf.py
        self.config.init_values()

        # check the Sphinx version if requested
        if self.config.needs_sphinx and \
           self.config.needs_sphinx > sphinx.__version__[:3]:
            raise VersionRequirementError(
                'This project needs at least Sphinx v%s and therefore cannot '
                'be built with this version.' % self.config.needs_sphinx)

        # set up translation infrastructure
        self._init_i18n()
        # set up the build environment
        self._init_env(freshenv)
        # set up the builder
        self._init_builder(buildername)

    def _init_i18n(self):
        """
        Load translated strings from the configured localedirs if
        enabled in the configuration.
        """
        if self.config.language is not None:
            self.info(bold('loading translations [%s]... ' %
                           self.config.language), nonl=True)
            locale_dirs = [None, path.join(package_dir, 'locale')] + \
                [path.join(self.srcdir, x) for x in self.config.locale_dirs]
        else:
            locale_dirs = []
        self.translator, has_translation = locale.init(locale_dirs,
                                                       self.config.language)
        if self.config.language is not None:
            if has_translation:
                self.info('done')
            else:
                self.info('locale not available')

    def _init_env(self, freshenv):
        if freshenv:
            self.env = BuildEnvironment(self.srcdir, self.doctreedir,
                                        self.config)
            self.env.find_files(self.config)
            for domain in self.domains.keys():
                self.env.domains[domain] = self.domains[domain](self.env)
        else:
            try:
                self.info(bold('loading pickled environment... '), nonl=True)
                self.env = BuildEnvironment.frompickle(self.config,
                    path.join(self.doctreedir, ENV_PICKLE_FILENAME))
                self.env.domains = {}
                for domain in self.domains.keys():
                    # this can raise if the data version doesn't fit
                    self.env.domains[domain] = self.domains[domain](self.env)
                self.info('done')
            except Exception, err:
                if type(err) is IOError and err.errno == ENOENT:
                    self.info('not yet created')
                else:
                    self.info('failed: %s' % err)
                return self._init_env(freshenv=True)

        self.env.set_warnfunc(self.warn)

    def _init_builder(self, buildername):
        if buildername is None:
            print >>self._status, 'No builder selected, using default: html'
            buildername = 'html'
        if buildername not in self.builderclasses:
            raise SphinxError('Builder name %s not registered' % buildername)

        builderclass = self.builderclasses[buildername]
        if isinstance(builderclass, tuple):
            # builtin builder
            mod, cls = builderclass
            builderclass = getattr(
                __import__('sphinx.builders.' + mod, None, None, [cls]), cls)
        self.builder = builderclass(self)
        self.emit('builder-inited')

    def build(self, force_all=False, filenames=None):
        try:
            if force_all:
                self.builder.build_all()
            elif filenames:
                self.builder.build_specific(filenames)
            else:
                self.builder.build_update()
        except Exception, err:
            self.emit('build-finished', err)
            raise
        else:
            self.emit('build-finished', None)
        self.builder.cleanup()

    def warn(self, message, location=None, prefix='WARNING: '):
        if isinstance(location, tuple):
            docname, lineno = location
            if docname:
                location = '%s:%s' % (self.env.doc2path(docname), lineno or '')
            else:
                location = None
        warntext = location and '%s: %s%s\n' % (location, prefix, message) or \
                   '%s%s\n' % (prefix, message)
        if self.warningiserror:
            raise SphinxWarning(warntext)
        self._warncount += 1
        try:
            self._warning.write(warntext)
        except UnicodeEncodeError:
            encoding = getattr(self._warning, 'encoding', 'ascii') or 'ascii'
            self._warning.write(warntext.encode(encoding, 'replace'))

    def info(self, message='', nonl=False):
        try:
            self._status.write(message)
        except UnicodeEncodeError:
            encoding = getattr(self._status, 'encoding', 'ascii') or 'ascii'
            self._status.write(message.encode(encoding, 'replace'))
        if not nonl:
            self._status.write('\n')
        self._status.flush()

    # general extensibility interface

    def setup_extension(self, extension):
        """Import and setup a Sphinx extension module. No-op if called twice."""
        if extension in self._extensions:
            return
        try:
            mod = __import__(extension, None, None, ['setup'])
        except ImportError, err:
            raise ExtensionError('Could not import extension %s' % extension,
                                 err)
        if not hasattr(mod, 'setup'):
            self.warn('extension %r has no setup() function; is it really '
                      'a Sphinx extension module?' % extension)
        else:
            try:
                mod.setup(self)
            except VersionRequirementError, err:
                # add the extension name to the version required
                raise VersionRequirementError(
                    'The %s extension used by this project needs at least '
                    'Sphinx v%s; it therefore cannot be built with this '
                    'version.' % (extension, err))
        self._extensions[extension] = mod

    def require_sphinx(self, version):
        # check the Sphinx version if requested
        if version > sphinx.__version__[:3]:
            raise VersionRequirementError(version)

    def import_object(self, objname, source=None):
        """Import an object from a 'module.name' string."""
        try:
            module, name = objname.rsplit('.', 1)
        except ValueError, err:
            raise ExtensionError('Invalid full object name %s' % objname +
                                 (source and ' (needed for %s)' % source or ''),
                                 err)
        try:
            return getattr(__import__(module, None, None, [name]), name)
        except ImportError, err:
            raise ExtensionError('Could not import %s' % module +
                                 (source and ' (needed for %s)' % source or ''),
                                 err)
        except AttributeError, err:
            raise ExtensionError('Could not find %s' % objname +
                                 (source and ' (needed for %s)' % source or ''),
                                 err)

    # event interface

    def _validate_event(self, event):
        event = intern(event)
        if event not in self._events:
            raise ExtensionError('Unknown event name: %s' % event)

    def connect(self, event, callback):
        self._validate_event(event)
        listener_id = self.next_listener_id
        if event not in self._listeners:
            self._listeners[event] = {listener_id: callback}
        else:
            self._listeners[event][listener_id] = callback
        self.next_listener_id += 1
        return listener_id

    def disconnect(self, listener_id):
        for event in self._listeners.itervalues():
            event.pop(listener_id, None)

    def emit(self, event, *args):
        results = []
        if event in self._listeners:
            for _, callback in self._listeners[event].iteritems():
                results.append(callback(self, *args))
        return results

    def emit_firstresult(self, event, *args):
        for result in self.emit(event, *args):
            if result is not None:
                return result
        return None

    # registering addon parts

    def add_builder(self, builder):
        if not hasattr(builder, 'name'):
            raise ExtensionError('Builder class %s has no "name" attribute'
                                 % builder)
        if builder.name in self.builderclasses:
            if isinstance(self.builderclasses[builder.name], tuple):
                raise ExtensionError('Builder %r is a builtin builder' %
                                     builder.name)
            else:
                raise ExtensionError(
                    'Builder %r already exists (in module %s)' % (
                    builder.name, self.builderclasses[builder.name].__module__))
        self.builderclasses[builder.name] = builder

    def add_config_value(self, name, default, rebuild):
        if name in self.config.values:
            raise ExtensionError('Config value %r already present' % name)
        if rebuild in (False, True):
            rebuild = rebuild and 'env' or ''
        self.config.values[name] = (default, rebuild)

    def add_event(self, name):
        if name in self._events:
            raise ExtensionError('Event %r already present' % name)
        self._events[name] = ''

    def add_node(self, node, **kwds):
        nodes._add_node_class_names([node.__name__])
        for key, val in kwds.iteritems():
            try:
                visit, depart = val
            except ValueError:
                raise ExtensionError('Value for key %r must be a '
                                     '(visit, depart) function tuple' % key)
            if key == 'html':
                from sphinx.writers.html import HTMLTranslator as translator
            elif key == 'latex':
                from sphinx.writers.latex import LaTeXTranslator as translator
            elif key == 'text':
                from sphinx.writers.text import TextTranslator as translator
            elif key == 'man':
                from sphinx.writers.manpage import ManualPageTranslator \
                    as translator
            else:
                # ignore invalid keys for compatibility
                continue
            setattr(translator, 'visit_'+node.__name__, visit)
            if depart:
                setattr(translator, 'depart_'+node.__name__, depart)

    def _directive_helper(self, obj, content=None, arguments=None, **options):
        if isinstance(obj, (types.FunctionType, types.MethodType)):
            obj.content = content
            obj.arguments = arguments or (0, 0, False)
            obj.options = options
            return convert_directive_function(obj)
        else:
            if content or arguments or options:
                raise ExtensionError('when adding directive classes, no '
                                     'additional arguments may be given')
            return obj

    def add_directive(self, name, obj, content=None, arguments=None, **options):
        directives.register_directive(
            name, self._directive_helper(obj, content, arguments, **options))

    def add_role(self, name, role):
        roles.register_local_role(name, role)

    def add_generic_role(self, name, nodeclass):
        # don't use roles.register_generic_role because it uses
        # register_canonical_role
        role = roles.GenericRole(name, nodeclass)
        roles.register_local_role(name, role)

    def add_domain(self, domain):
        if domain.name in self.domains:
            raise ExtensionError('domain %s already registered' % domain.name)
        self.domains[domain.name] = domain

    def override_domain(self, domain):
        if domain.name not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain.name)
        if not issubclass(domain, self.domains[domain.name]):
            raise ExtensionError('new domain not a subclass of registered '
                                 'domain' % domain.name)
        self.domains[domain.name] = domain

    def add_directive_to_domain(self, domain, name, obj,
                                content=None, arguments=None, **options):
        if domain not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain)
        self.domains[domain].directives[name] = \
            self._directive_helper(obj, content, arguments, **options)

    def add_role_to_domain(self, domain, name, role):
        if domain not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain)
        self.domains[domain].roles[name] = role

    def add_index_to_domain(self, domain, name, localname, shortname, func):
        if domain not in self.domains:
            raise ExtensionError('domain %s not yet registered' % domain)
        self.domains[domain].indices.append((name, localname, shortname))
        setattr(self.domains[domain], 'get_%s_index' % name, func)

    def add_object_type(self, directivename, rolename, indextemplate='',
                        parse_node=None, ref_nodeclass=None, objname='',
                        doc_field_types=[]):
        StandardDomain.object_types[directivename] = \
            ObjType(objname or directivename, rolename)
        # create a subclass of GenericObject as the new directive
        new_directive = type(directivename, (GenericObject, object),
                             {'indextemplate': indextemplate,
                              'parse_node': staticmethod(parse_node),
                              'doc_field_types': doc_field_types})
        StandardDomain.directives[directivename] = new_directive
        # XXX support more options?
        StandardDomain.roles[rolename] = XRefRole(innernodeclass=ref_nodeclass)

    # backwards compatible alias
    add_description_unit = add_object_type

    def add_crossref_type(self, directivename, rolename, indextemplate='',
                          ref_nodeclass=None, objname=''):
        StandardDomain.object_types[directivename] = \
            ObjType(objname or directivename, rolename)
        # create a subclass of Target as the new directive
        new_directive = type(directivename, (Target, object),
                             {'indextemplate': indextemplate})
        StandardDomain.directives[directivename] = new_directive
        # XXX support more options?
        StandardDomain.roles[rolename] = XRefRole(innernodeclass=ref_nodeclass)

    def add_transform(self, transform):
        SphinxStandaloneReader.transforms.append(transform)

    def add_javascript(self, filename):
        from sphinx.builders.html import StandaloneHTMLBuilder
        if '://' in filename:
            StandaloneHTMLBuilder.script_files.append(filename)
        else:
            StandaloneHTMLBuilder.script_files.append(
                posixpath.join('_static', filename))

    def add_stylesheet(self, filename):
        from sphinx.builders.html import StandaloneHTMLBuilder
        StandaloneHTMLBuilder.css_files.append(
            posixpath.join('_static', filename))

    def add_lexer(self, alias, lexer):
        from sphinx.highlighting import lexers
        if lexers is None:
            return
        lexers[alias] = lexer

    def add_autodocumenter(self, cls):
        from sphinx.ext import autodoc
        autodoc.add_documenter(cls)
        self.add_directive('auto' + cls.objtype, autodoc.AutoDirective)

    def add_autodoc_attrgetter(self, type, getter):
        from sphinx.ext import autodoc
        autodoc.AutoDirective._special_attrgetters[type] = getter


class TemplateBridge(object):
    """
    This class defines the interface for a "template bridge", that is, a class
    that renders templates given a template name and a context.
    """

    def init(self, builder, theme=None, dirs=None):
        """
        Called by the builder to initialize the template system.

        *builder* is the builder object; you'll probably want to look at the
        value of ``builder.config.templates_path``.

        *theme* is a :class:`sphinx.theming.Theme` object or None; in the latter
        case, *dirs* can be list of fixed directories to look for templates.
        """
        raise NotImplementedError('must be implemented in subclasses')

    def newest_template_mtime(self):
        """
        Called by the builder to determine if output files are outdated
        because of template changes.  Return the mtime of the newest template
        file that was changed.  The default implementation returns ``0``.
        """
        return 0

    def render(self, template, context):
        """
        Called by the builder to render a template given as a filename with a
        specified context (a Python dictionary).
        """
        raise NotImplementedError('must be implemented in subclasses')

    def render_string(self, template, context):
        """
        Called by the builder to render a template given as a string with a
        specified context (a Python dictionary).
        """
        raise NotImplementedError('must be implemented in subclasses')
