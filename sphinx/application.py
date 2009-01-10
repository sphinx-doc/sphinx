# -*- coding: utf-8 -*-
"""
    sphinx.application
    ~~~~~~~~~~~~~~~~~~

    Sphinx application object.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import posixpath
from cStringIO import StringIO

from docutils import nodes
from docutils.parsers.rst import directives, roles

import sphinx
from sphinx.roles import xfileref_role, innernodetypes
from sphinx.config import Config
from sphinx.builders import BUILTIN_BUILDERS
from sphinx.directives import desc_directive, target_directive, \
     additional_xref_types
from sphinx.environment import SphinxStandaloneReader
from sphinx.util.console import bold


class SphinxError(Exception):
    """
    Base class for Sphinx errors that are shown to the user in a nicer
    way than normal exceptions.
    """
    category = 'Sphinx error'

class ExtensionError(SphinxError):
    """Raised if something's wrong with the configuration."""
    category = 'Extension error'

    def __init__(self, message, orig_exc=None):
        super(ExtensionError, self).__init__(message)
        self.orig_exc = orig_exc

    def __repr__(self):
        if self.orig_exc:
            return '%s(%r, %r)' % (self.__class__.__name__,
                                   self.message, self.orig_exc)
        return '%s(%r)' % (self.__class__.__name__, self.message)

    def __str__(self):
        parent_str = super(ExtensionError, self).__str__()
        if self.orig_exc:
            return '%s (exception: %s)' % (parent_str, self.orig_exc)
        return parent_str


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
                 confoverrides, status, warning=sys.stderr, freshenv=False):
        self.next_listener_id = 0
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

        self._events = events.copy()

        # status code for command-line application
        self.statuscode = 0

        # read config
        self.config = Config(confdir, CONFIG_FILENAME, confoverrides)

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

        self.info(bold('Sphinx v%s, building %s' % (sphinx.__released__,
                                                    buildername)))

        builderclass = self.builderclasses[buildername]
        if isinstance(builderclass, tuple):
            # builtin builder
            mod, cls = builderclass
            builderclass = getattr(
                __import__('sphinx.builders.' + mod, None, None, [cls]), cls)
        self.builder = builderclass(self, freshenv=freshenv)
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

    def warn(self, message):
        self._warncount += 1
        try:
            self._warning.write('WARNING: %s\n' % message)
        except UnicodeEncodeError:
            encoding = getattr(self._warning, 'encoding', 'ascii')
            self._warning.write(('WARNING: %s\n' % message).encode(encoding,
                                                                   'replace'))

    def info(self, message='', nonl=False):
        try:
            self._status.write(message)
        except UnicodeEncodeError:
            encoding = getattr(self._status, 'encoding', 'ascii')
            self._status.write(message.encode(encoding, 'replace'))
        if not nonl:
            self._status.write('\n')
        self._status.flush()

    # general extensibility interface

    def setup_extension(self, extension):
        """Import and setup a Sphinx extension module."""
        try:
            mod = __import__(extension, None, None, ['setup'])
        except ImportError, err:
            raise ExtensionError('Could not import extension %s' % extension,
                                 err)
        if hasattr(mod, 'setup'):
            mod.setup(self)

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

    def add_config_value(self, name, default, rebuild_env):
        if name in self.config.values:
            raise ExtensionError('Config value %r already present' % name)
        self.config.values[name] = (default, rebuild_env)

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

    def add_directive(self, name, func, content, arguments, **options):
        func.content = content
        func.arguments = arguments
        func.options = options
        directives.register_directive(name, func)

    def add_role(self, name, role):
        roles.register_canonical_role(name, role)

    def add_description_unit(self, directivename, rolename, indextemplate='',
                             parse_node=None, ref_nodeclass=None):
        additional_xref_types[directivename] = (rolename, indextemplate,
                                                parse_node)
        directives.register_directive(directivename, desc_directive)
        roles.register_canonical_role(rolename, xfileref_role)
        if ref_nodeclass is not None:
            innernodetypes[rolename] = ref_nodeclass

    def add_crossref_type(self, directivename, rolename, indextemplate='',
                          ref_nodeclass=None):
        additional_xref_types[directivename] = (rolename, indextemplate, None)
        directives.register_directive(directivename, target_directive)
        roles.register_canonical_role(rolename, xfileref_role)
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


class TemplateBridge(object):
    """
    This class defines the interface for a "template bridge", that is, a class
    that renders templates given a template name and a context.
    """

    def init(self, builder):
        """
        Called by the builder to initialize the template system.  *builder*
        is the builder object; you'll probably want to look at the value of
        ``builder.config.templates_path``.
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
        Called by the builder to render a *template* with a specified
        context (a Python dictionary).
        """
        raise NotImplementedError('must be implemented in subclasses')
