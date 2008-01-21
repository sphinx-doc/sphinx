# -*- coding: utf-8 -*-
"""
    sphinx.extension
    ~~~~~~~~~~~~~~~~

    Gracefully adapted from the TextPress event system by Armin.

    :copyright: 2008 by Georg Brandl, Armin Ronacher.
    :license: BSD.
"""

from sphinx.config import ConfigError


def import_object(objname, source=None):
    """Import an object from a 'module.name' string."""
    try:
        module, name = objname.rsplit('.', 1)
    except ValueError, err:
        raise ConfigError('Invalid full object name %s' % objname +
                          (source and ' (needed for %s)' % source or ''), err)
    try:
        return getattr(__import__(module, None, None, [name]), name)
    except ImportError, err:
        raise ConfigError('Could not import %s' % module +
                          (source and ' (needed for %s)' % source or ''), err)
    except AttributeError, err:
        raise ConfigError('Could not find %s' % objname +
                          (source and ' (needed for %s)' % source or ''), err)


# List of all known events. Maps name to arguments description.
events = {
    'builder-created' : 'builder instance',
    'doctree-read' : 'the doctree before being pickled',
}

class EventManager(object):
    """
    Helper class that handles event listeners and events.

    This is *not* a public interface. Always use the emit_event()
    functions to access it or the connect_event() / disconnect_event()
    functions on the application.
    """

    def __init__(self):
        self.next_listener_id = 0
        self._listeners = {}

    def _validate(self, event):
        event = intern(event)
        if event not in events:
            raise RuntimeError('unknown event name: %s' % event)

    def connect(self, event, callback):
        self._validate(event)
        listener_id = self.next_listener_id
        if event not in self._listeners:
            self._listeners[event] = {listener_id: callback}
        else:
            self._listeners[event][listener_id] = callback
        self.next_listener_id += 1
        return listener_id

    def remove(self, listener_id):
        for event in self._listeners:
            event.pop(listener_id, None)

    def emit(self, event, *args):
        self._validate(event)
        if event in self._listeners:
            for listener_id, callback in self._listeners[event].iteritems():
                yield listener_id, callback(*args)


class DummyEventManager(EventManager):
    def connect(self, event, callback):
        self._validate(event)
    def remove(self, listener_id):
        pass
    def emit(self, event, *args):
        self._validate(event)
