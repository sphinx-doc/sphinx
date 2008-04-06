# -*- coding: utf-8 -*-
"""
    sphinx.application
    ~~~~~~~~~~~~~~~~~~

    Sphinx application object.

    Gracefully adapted from the TextPress system by Armin.


    :copyright: 2008 by Georg Brandl, Armin Ronacher.
    :license: BSD.
"""

import sys

from docutils import nodes
from docutils.parsers.rst import directives, roles

import sphinx
from sphinx.roles import xfileref_role, innernodetypes
from sphinx.config import Config
from sphinx.builder import builtin_builders
from sphinx.directives import desc_directive, target_directive, additional_xref_types
from sphinx.util.console import bold


class ExtensionError(Exception):
    """Raised if something's wrong with the configuration."""

    def __init__(self, message, orig_exc=None):
        self.message = message
        self.orig_exc = orig_exc

    def __repr__(self):
        if self.orig_exc:
            return '%s(%r, %r)' % (self.__class__.__name__,
                                   self.message, self.orig_exc)
        return '%s(%r)' % (self.__class__.__name__, self.message)

    def __str__(self):
        if self.orig_exc:
            return '%s (exception: %s)' % (self.message, self.orig_exc)
        return self.message


# List of all known core events. Maps name to arguments description.
events = {
    'builder-inited': '',
    'doctree-read' : 'the doctree before being pickled',
    'doctree-resolved' : 'the doctree, the docname',
}

class Sphinx(object):

    def __init__(self, srcdir, outdir, doctreedir, buildername,
                 confoverrides, status, warning=sys.stderr, freshenv=False):
        self.next_listener_id = 0
        self._listeners = {}
        self.builderclasses = builtin_builders.copy()
        self.builder = None

        self.srcdir = srcdir
        self.outdir = outdir
        self.doctreedir = doctreedir

        self._status = status
        self._warning = warning
        self._warncount = 0

        self._events = events.copy()

        # read config
        self.config = Config(srcdir, 'conf.py')
        if confoverrides:
            for key, val in confoverrides.items():
                setattr(self.config, key, val)

        # load all extension modules
        for extension in getattr(self.config, 'extensions', ()):
            self.setup_extension(extension)
        # the config file itself can be an extension
        if hasattr(self.config, 'setup'):
            self.config.setup(self)

        # this must happen after loading extension modules, since they
        # can add custom config values
        self.config.init_defaults()

        if buildername is None:
            print >>status, 'No builder selected, using default: html'
            buildername = 'html'
        if buildername not in self.builderclasses:
            print >>warning, 'Builder name %s not registered' % buildername
            return

        self.info(bold('Sphinx v%s, building %s' % (sphinx.__version__, buildername)))

        builderclass = self.builderclasses[buildername]
        self.builder = builderclass(self, freshenv=freshenv)
        self.emit('builder-inited')

    def warn(self, message):
        self._warncount += 1
        self._warning.write('WARNING: %s\n' % message)

    def info(self, message='', nonl=False):
        if nonl:
            self._status.write(message)
        else:
            self._status.write(message + '\n')
        self._status.flush()

    # general extensibility interface

    def setup_extension(self, extension):
        """Import and setup a Sphinx extension module."""
        try:
            mod = __import__(extension, None, None, ['setup'])
        except ImportError, err:
            raise ExtensionError('Could not import extension %s' % extension, err)
        if hasattr(mod, 'setup'):
            mod.setup(self)

    def import_object(self, objname, source=None):
        """Import an object from a 'module.name' string."""
        try:
            module, name = objname.rsplit('.', 1)
        except ValueError, err:
            raise ExtensionError('Invalid full object name %s' % objname +
                                 (source and ' (needed for %s)' % source or ''), err)
        try:
            return getattr(__import__(module, None, None, [name]), name)
        except ImportError, err:
            raise ExtensionError('Could not import %s' % module +
                                 (source and ' (needed for %s)' % source or ''), err)
        except AttributeError, err:
            raise ExtensionError('Could not find %s' % objname +
                                 (source and ' (needed for %s)' % source or ''), err)

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
        for event in self._listeners:
            event.pop(listener_id, None)

    def emit(self, event, *args):
        result = []
        if event in self._listeners:
            for _, callback in self._listeners[event].iteritems():
                result.append(callback(self, *args))
        return result

    # registering addon parts

    def add_builder(self, builder):
        if not hasattr(builder, 'name'):
            raise ExtensionError('Builder class %s has no "name" attribute' % builder)
        if builder.name in self.builderclasses:
            raise ExtensionError('Builder %r already exists (in module %s)' % (
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

    def add_node(self, node):
        nodes._add_node_class_names([node.__name__])

    def add_directive(self, name, func, content, arguments, **options):
        func.content = content
        func.arguments = arguments
        func.options = options
        directives.register_directive(name, func)

    def add_role(self, name, role):
        roles.register_canonical_role(name, role)

    def add_description_unit(self, directivename, rolename, indextemplate='',
                             parse_node=None, ref_nodeclass=None):
        additional_xref_types[directivename] = (rolename, indextemplate, parse_node)
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
