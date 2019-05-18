"""
    sphinx.events
    ~~~~~~~~~~~~~

    Sphinx core events.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from collections import OrderedDict, defaultdict

from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.errors import ExtensionError
from sphinx.locale import __
from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, Callable, Dict, List  # NOQA
    from sphinx.application import Sphinx  # NOQA

logger = logging.getLogger(__name__)


# List of all known core events. Maps name to arguments description.
core_events = {
    'builder-inited': '',
    'config-inited': 'config',
    'env-get-outdated': 'env, added, changed, removed',
    'env-get-updated': 'env',
    'env-purge-doc': 'env, docname',
    'env-before-read-docs': 'env, docnames',
    'env-check-consistency': 'env',
    'source-read': 'docname, source text',
    'doctree-read': 'the doctree before being pickled',
    'env-merge-info': 'env, read docnames, other env instance',
    'missing-reference': 'env, node, contnode',
    'doctree-resolved': 'doctree, docname',
    'env-updated': 'env',
    'html-collect-pages': 'builder',
    'html-page-context': 'pagename, context, doctree or None',
    'build-finished': 'exception',
}


class EventManager:
    """Event manager for Sphinx."""

    def __init__(self, app=None):
        # type: (Sphinx) -> None
        if app is None:
            warnings.warn('app argument is required for EventManager.',
                          RemovedInSphinx40Warning)
        self.app = app
        self.events = core_events.copy()
        self.listeners = defaultdict(OrderedDict)  # type: Dict[str, Dict[int, Callable]]
        self.next_listener_id = 0

    def add(self, name):
        # type: (str) -> None
        """Register a custom Sphinx event."""
        if name in self.events:
            raise ExtensionError(__('Event %r already present') % name)
        self.events[name] = ''

    def connect(self, name, callback):
        # type: (str, Callable) -> int
        """Connect a handler to specific event."""
        if name not in self.events:
            raise ExtensionError(__('Unknown event name: %s') % name)

        listener_id = self.next_listener_id
        self.next_listener_id += 1
        self.listeners[name][listener_id] = callback
        return listener_id

    def disconnect(self, listener_id):
        # type: (int) -> None
        """Disconnect a handler."""
        for event in self.listeners.values():
            event.pop(listener_id, None)

    def emit(self, name, *args):
        # type: (str, Any) -> List
        """Emit a Sphinx event."""
        try:
            logger.debug('[app] emitting event: %r%s', name, repr(args)[:100])
        except Exception:
            # not every object likes to be repr()'d (think
            # random stuff coming via autodoc)
            pass

        results = []
        for callback in self.listeners[name].values():
            if self.app is None:
                # for compatibility; RemovedInSphinx40Warning
                results.append(callback(*args))
            else:
                results.append(callback(self.app, *args))
        return results

    def emit_firstresult(self, name, *args):
        # type: (str, Any) -> Any
        """Emit a Sphinx event and returns first result.

        This returns the result of the first handler that doesn't return ``None``.
        """
        for result in self.emit(name, *args):
            if result is not None:
                return result
        return None
