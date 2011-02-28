# -*- coding: utf-8 -*-
"""
    test_application
    ~~~~~~~~~~~~~~~~

    Test the Sphinx class.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from StringIO import StringIO

from sphinx.application import ExtensionError

from util import *


@with_app()
def test_events(app):
    def empty(): pass
    raises_msg(ExtensionError, "Unknown event name: invalid",
               app.connect, "invalid", empty)


    app.add_event("my_event")
    raises_msg(ExtensionError, "Event 'my_event' already present",
               app.add_event, "my_event")

    def mock_callback(a_app, *args):
        assert a_app is app
        assert emit_args == args
        return "ret"
    emit_args = (1, 3, "string")
    listener_id = app.connect("my_event", mock_callback)
    assert app.emit("my_event", *emit_args) == ["ret"], "Callback not called"

    app.disconnect(listener_id)
    assert app.emit("my_event", *emit_args) == [], \
        "Callback called when disconnected"


def test_output():
    status, warnings = StringIO(), StringIO()
    app = TestApp(status=status, warning=warnings)
    try:
        status.truncate(0) # __init__ writes to status
        status.seek(0)
        app.info("Nothing here...")
        assert status.getvalue() == "Nothing here...\n"
        status.truncate(0)
        status.seek(0)
        app.info("Nothing here...", True)
        assert status.getvalue() == "Nothing here..."

        old_count = app._warncount
        app.warn("Bad news!")
        assert warnings.getvalue() == "WARNING: Bad news!\n"
        assert app._warncount == old_count + 1
    finally:
        app.cleanup()


def test_extensions():
    status, warnings = StringIO(), StringIO()
    app = TestApp(status=status, warning=warnings)
    try:
        app.setup_extension('shutil')
        assert warnings.getvalue().startswith("WARNING: extension 'shutil'")
    finally:
        app.cleanup()
