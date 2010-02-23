# -*- coding: utf-8 -*-
"""
    sphinx.application
    ~~~~~~~~~~~~~~~~~~

    Sphinx application object.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import types
import posixpath
from cStringIO import StringIO

from docutils import nodes
from docutils.parsers.rst import directives, roles

import sphinx
from sphinx.roles import xfileref_role, innernodetypes
from sphinx.config import Config
from sphinx.errors import SphinxError, SphinxWarning, ExtensionError
from sphinx.builders import BUILTIN_BUILDERS
from sphinx.directives import GenericDesc, Target, additional_xref_types
from sphinx.environment import SphinxStandaloneReader
from sphinx.util import pycompat  # imported for side-effects
from sphinx.util.tags import Tags
from sphinx.util.compat import Directive, directive_dwim
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
    'html-page-context': 'pagename, context, doctree or None',
    'build-finished': 'exception',
}

CONFIG_FILENAME = 'conf.py'


class Sphinx(object):

    def __init__(self, srcdir, confdir, outdir, doctreedir, buildername,
                 confoverrides, status, warning=sys.stderr, freshenv=False,
                 warningiserror=False, tags=None):
        self.next_listener_id = 0
        self._extensions = {}
        self._listeners = {}
        self.builderclasses = BUILTIN_BUILDERS.copy()
        self.builder = None

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
        self.config = Config(confdir, CONFIG_FILENAME, confoverrides, self.tags)
        self.config.check_unicode(self.warn)

        # set confdir to srcdir if -C given (!= no confdir); a few pieces
        # of code expect a confdir to be set
        if self.confdir is None:
            self.confdir = self.srcdir

        # load all extension modules
        for extension in self.config.extensions:
            self.setup_extension(extension)
        # the config file itself can be an extension
        if self.config.setup:
            self.config.setup(self)

        # now that we know all config values, collect them from conf.py
        self.config.init_values()

        if buildername is None:
            print >>status, 'No builder selected, using default: html'
            buildername = 'html'
        if buildername not in self.builderclasses:
            raise SphinxError('Builder name %s not registered' % buildername)

        builderclass = self.builderclasses[buildername]
        if isinstance(builderclass, tuple):
            # builtin builder
            mod, cls = builderclass
            builderclass = getattr(
                __import__('sphinx.builders.' + mod, None, None, [cls]), cls)
        self.builder = builderclass(self, freshenv=freshenv)
        self.builder.tags = self.tags
        self.builder.tags.add(self.builder.format)
        self.emit('builder-inited')

    def build(self, all_files, filenames):
        try:
            if all_files:
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
            mod.setup(self)
        self._extensions[extension] = mod

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
        result = []
        if event in self._listeners:
            for _, callback in self._listeners[event].iteritems():
                result.append(callback(self, *args))
        return result

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
            else:
                # ignore invalid keys for compatibility
                continue
            setattr(translator, 'visit_'+node.__name__, visit)
            if depart:
                setattr(translator, 'depart_'+node.__name__, depart)

    def add_directive(self, name, obj, content=None, arguments=None, **options):
        if isinstance(obj, clstypes) and issubclass(obj, Directive):
            if content or arguments or options:
                raise ExtensionError('when adding directive classes, no '
                                     'additional arguments may be given')
            directives.register_directive(name, directive_dwim(obj))
        else:
            obj.content = content
            obj.arguments = arguments
            obj.options = options
            directives.register_directive(name, obj)

    def add_role(self, name, role):
        roles.register_local_role(name, role)

    def add_generic_role(self, name, nodeclass):
        # don't use roles.register_generic_role because it uses
        # register_canonical_role
        role = roles.GenericRole(name, nodeclass)
        roles.register_local_role(name, role)

    def add_description_unit(self, directivename, rolename, indextemplate='',
                             parse_node=None, ref_nodeclass=None):
        additional_xref_types[directivename] = (rolename, indextemplate,
                                                parse_node)
        directives.register_directive(directivename,
                                      directive_dwim(GenericDesc))
        roles.register_local_role(rolename, xfileref_role)
        if ref_nodeclass is not None:
            innernodetypes[rolename] = ref_nodeclass

    def add_crossref_type(self, directivename, rolename, indextemplate='',
                          ref_nodeclass=None):
        additional_xref_types[directivename] = (rolename, indextemplate, None)
        directives.register_directive(directivename, directive_dwim(Target))
        roles.register_local_role(rolename, xfileref_role)
        if ref_nodeclass is not None:
            innernodetypes[rolename] = ref_nodeclass

    def add_transform(self, transform):
        SphinxStandaloneReader.transforms.append(transform)

    def add_javascript(self, filename):
        from sphinx.builders.html import StandaloneHTMLBuilder
        StandaloneHTMLBuilder.script_files.append(
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
