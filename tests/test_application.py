# -*- coding: utf-8 -*-
"""
    test_application
    ~~~~~~~~~~~~~~~~

    Test the Sphinx class.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import codecs

from docutils import nodes

from sphinx.application import ExtensionError
from sphinx.domains import Domain

from util import strip_escseq
import pytest


def test_events(app, status, warning):
    def empty():
        pass
    with pytest.raises(ExtensionError) as excinfo:
        app.connect("invalid", empty)
    assert "Unknown event name: invalid" in str(excinfo.value)

    app.add_event("my_event")
    with pytest.raises(ExtensionError) as excinfo:
        app.add_event("my_event")
    assert "Event 'my_event' already present" in str(excinfo.value)

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


def test_emit_with_nonascii_name_node(app, status, warning):
    node = nodes.section(names=[u'\u65e5\u672c\u8a9e'])
    app.emit('my_event', node)


def test_output(app, status, warning):
    # info with newline
    status.truncate(0)  # __init__ writes to status
    status.seek(0)
    app.info("Nothing here...")
    assert status.getvalue() == "Nothing here...\n"
    # info without newline
    status.truncate(0)
    status.seek(0)
    app.info("Nothing here...", True)
    assert status.getvalue() == "Nothing here..."

    # warning
    old_count = app._warncount
    app.warn("Bad news!")
    assert strip_escseq(warning.getvalue()) == "WARNING: Bad news!\n"
    assert app._warncount == old_count + 1


def test_output_with_unencodable_char(app, status, warning):

    class StreamWriter(codecs.StreamWriter):
        def write(self, object):
            self.stream.write(object.encode('cp1252').decode('cp1252'))

    app._status = StreamWriter(status)

    # info with UnicodeEncodeError
    status.truncate(0)
    status.seek(0)
    app.info(u"unicode \u206d...")
    assert status.getvalue() == "unicode ?...\n"


def test_extensions(app, status, warning):
    app.setup_extension('shutil')
    assert strip_escseq(warning.getvalue()).startswith("WARNING: extension 'shutil'")


def test_extension_in_blacklist(app, status, warning):
    app.setup_extension('sphinxjp.themecore')
    msg = strip_escseq(warning.getvalue())
    assert msg.startswith("WARNING: the extension 'sphinxjp.themecore' was")


def test_domain_override(app, status, warning):
    class A(Domain):
        name = 'foo'

    class B(A):
        name = 'foo'

    class C(Domain):
        name = 'foo'

    # No domain know named foo.
    with pytest.raises(ExtensionError) as excinfo:
        app.override_domain(A)
    assert 'domain foo not yet registered' in str(excinfo.value)

    assert app.add_domain(A) is None
    assert app.override_domain(B) is None
    with pytest.raises(ExtensionError) as excinfo:
        app.override_domain(C)
    assert 'new domain not a subclass of registered foo domain' in str(excinfo.value)


@pytest.mark.sphinx(testroot='add_source_parser')
def test_add_source_parser(app, status, warning):
    assert set(app.config.source_suffix) == set(['.rst', '.md', '.test'])
    assert set(app.config.source_parsers.keys()) == set(['.md', '.test'])
    assert app.config.source_parsers['.md'].__name__ == 'DummyMarkdownParser'
    assert app.config.source_parsers['.test'].__name__ == 'TestSourceParser'


@pytest.mark.sphinx(testroot='add_source_parser-conflicts-with-users-setting')
def test_add_source_parser_conflicts_with_users_setting(app, status, warning):
    assert set(app.config.source_suffix) == set(['.rst', '.test'])
    assert set(app.config.source_parsers.keys()) == set(['.test'])
    assert app.config.source_parsers['.test'].__name__ == 'DummyTestParser'
