"""Test the EventManager class."""

import pytest

from sphinx.errors import ExtensionError
from sphinx.events import EventManager


def test_event_priority():
    result = []
    app = object()  # pass a dummy object as an app
    events = EventManager(app)  # type: ignore[arg-type]
    events.connect('builder-inited', lambda app: result.append(1), priority=500)
    events.connect('builder-inited', lambda app: result.append(2), priority=500)
    # earlier
    events.connect('builder-inited', lambda app: result.append(3), priority=200)
    # later
    events.connect('builder-inited', lambda app: result.append(4), priority=700)
    events.connect('builder-inited', lambda app: result.append(5), priority=500)

    events.emit('builder-inited')
    assert result == [3, 1, 2, 5, 4]


class FakeApp:
    def __init__(self, pdb: bool = False):
        self.pdb = pdb


def test_event_allowed_exceptions():
    def raise_error(app):
        raise RuntimeError

    app = FakeApp()  # pass a dummy object as an app
    events = EventManager(app)  # type: ignore[arg-type]
    events.connect('builder-inited', raise_error, priority=500)

    # all errors are converted to ExtensionError
    with pytest.raises(ExtensionError):
        events.emit('builder-inited')

    # Allow RuntimeError (pass-through)
    with pytest.raises(RuntimeError):
        events.emit('builder-inited', allowed_exceptions=(RuntimeError,))


def test_event_pdb():
    def raise_error(app):
        raise RuntimeError

    app = FakeApp(pdb=True)  # pass a dummy object as an app
    events = EventManager(app)  # type: ignore[arg-type]
    events.connect('builder-inited', raise_error, priority=500)

    # errors aren't converted
    with pytest.raises(RuntimeError):
        events.emit('builder-inited')

    # Allow RuntimeError (pass-through)
    with pytest.raises(RuntimeError):
        events.emit('builder-inited', allowed_exceptions=(RuntimeError,))
