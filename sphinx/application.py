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

from sphinx.config import Config
from sphinx.builder import builtin_builders


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


# List of all known events. Maps name to arguments description.
events = {
    'builder-inited': '',
    'doctree-read' : 'the doctree before being pickled',
    'doctree-resolved' : 'the doctree, the docname',
}

class Application(object):

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

        # read config
        self.config = Config(srcdir, 'conf.py')
        if confoverrides:
            for key, val in confoverrides.items():
                setattr(self.config, key, val)

        # load all extension modules
        for extension in getattr(self.config, 'extensions', ()):
            self.setup_extension(extension)

        # this must happen after loading extension modules, since they
        # can add custom config values
        self.config.init_defaults()

        if buildername is None:
            print >>status, 'No builder selected, using default: html'
            buildername = 'html'
        if buildername not in self.builderclasses:
            print >>warning, 'Builder name %s not registered' % buildername
            return

        builderclass = self.builderclasses[buildername]
        self.builder = builderclass(self, freshenv=freshenv)
        self.emit('builder-inited')

    def warn(self, message):
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
        if event not in events:
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
            raise ExtensionError('Config value %r already present')
        self.config.values[name] = (default, rebuild_env)

    def add_node(self, node):
        nodes._add_node_class_names([node.__name__])

    def add_directive(self, name, cls, content, arguments):
        cls.content = content
        cls.arguments = arguments
        directives.register_directive(name, cls)

    def add_role(self, name, role):
        roles.register_canonical_role(name, role)
