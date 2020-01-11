"""
    test_events
    ~~~~~~~~~~~

    Test the EventManager class.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.events import EventManager


def test_event_priority():
    result = []
    events = EventManager(object())  # pass an dummy object as an app
    events.connect('builder-inited', lambda app: result.append(1), priority = 500)
    events.connect('builder-inited', lambda app: result.append(2), priority = 500)
    events.connect('builder-inited', lambda app: result.append(3), priority = 200)  # eariler
    events.connect('builder-inited', lambda app: result.append(4), priority = 700)  # later
    events.connect('builder-inited', lambda app: result.append(5), priority = 500)

    events.emit('builder-inited')
    assert result == [3, 1, 2, 5, 4]
