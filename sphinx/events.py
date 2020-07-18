"""
    sphinx.events
    ~~~~~~~~~~~~~

    Sphinx core events.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import defaultdict
from operator import attrgetter
from typing import Any, Callable, Dict, List, NamedTuple, Tuple, Type
from typing import TYPE_CHECKING

from sphinx.errors import ExtensionError, SphinxError
from sphinx.locale import __
from sphinx.util import logging

if TYPE_CHECKING:
    from sphinx.application import Sphinx


logger = logging.getLogger(__name__)


class EventListener(NamedTuple):
    id: int
    handler: Callable
    priority: int


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

    def __init__(self, app: "Sphinx") -> None:
        self.app = app
        self.events = core_events.copy()
        self.listeners = defaultdict(list)  # type: Dict[str, List[EventListener]]
        self.next_listener_id = 0

    def add(self, name: str) -> None:
        """Register a custom Sphinx event."""
        if name in self.events:
            raise ExtensionError(__('Event %r already present') % name)
        self.events[name] = ''

    def connect(self, name: str, callback: Callable, priority: int) -> int:
        """Connect a handler to specific event."""
        if name not in self.events:
            raise ExtensionError(__('Unknown event name: %s') % name)

        listener_id = self.next_listener_id
        self.next_listener_id += 1
        self.listeners[name].append(EventListener(listener_id, callback, priority))
        return listener_id

    def disconnect(self, listener_id: int) -> None:
        """Disconnect a handler."""
        for listeners in self.listeners.values():
            for listener in listeners[:]:
                if listener.id == listener_id:
                    listeners.remove(listener)

    def emit(self, name: str, *args: Any,
             allowed_exceptions: Tuple[Type[Exception], ...] = ()) -> List:
        """Emit a Sphinx event."""
        try:
            logger.debug('[app] emitting event: %r%s', name, repr(args)[:100])
        except Exception:
            # not every object likes to be repr()'d (think
            # random stuff coming via autodoc)
            pass

        results = []
        listeners = sorted(self.listeners[name], key=attrgetter("priority"))
        for listener in listeners:
            try:
                results.append(listener.handler(self.app, *args))
            except allowed_exceptions:
                # pass through the errors specified as *allowed_exceptions*
                raise
            except SphinxError:
                raise
            except Exception as exc:
                raise ExtensionError(__("Handler %r for event %r threw an exception") %
                                     (listener.handler, name)) from exc
        return results

    def emit_firstresult(self, name: str, *args: Any,
                         allowed_exceptions: Tuple[Type[Exception], ...] = ()) -> Any:
        """Emit a Sphinx event and returns first result.

        This returns the result of the first handler that doesn't return ``None``.
        """
        for result in self.emit(name, *args, allowed_exceptions=allowed_exceptions):
            if result is not None:
                return result
        return None
