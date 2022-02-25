"""
    test_application
    ~~~~~~~~~~~~~~~~

    Test the Sphinx class.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from unittest.mock import Mock

import pytest
from docutils import nodes

from sphinx.errors import ExtensionError
from sphinx.testing.util import strip_escseq
from sphinx.util import logging


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
    node = nodes.section(names=['\u65e5\u672c\u8a9e'])
    app.emit('my_event', node)


def test_extensions(app, status, warning):
    app.setup_extension('shutil')
    warning = strip_escseq(warning.getvalue())
    assert "extension 'shutil' has no setup() function" in warning


def test_extension_in_blacklist(app, status, warning):
    app.setup_extension('sphinxjp.themecore')
    msg = strip_escseq(warning.getvalue())
    assert msg.startswith("WARNING: the extension 'sphinxjp.themecore' was")


@pytest.mark.sphinx(testroot='add_source_parser')
def test_add_source_parser(app, status, warning):
    assert set(app.config.source_suffix) == {'.rst', '.test'}

    # .rst; only in :confval:`source_suffix`
    assert '.rst' not in app.registry.get_source_parsers()
    assert app.registry.source_suffix['.rst'] is None

    # .test; configured by API
    assert app.registry.source_suffix['.test'] == 'test'
    assert 'test' in app.registry.get_source_parsers()
    assert app.registry.get_source_parsers()['test'].__name__ == 'TestSourceParser'


@pytest.mark.sphinx(testroot='extensions')
def test_add_is_parallel_allowed(app, status, warning):
    logging.setup(app, status, warning)

    assert app.is_parallel_allowed('read') is True
    assert app.is_parallel_allowed('write') is True
    assert warning.getvalue() == ''

    app.setup_extension('read_parallel')
    assert app.is_parallel_allowed('read') is True
    assert app.is_parallel_allowed('write') is True
    assert warning.getvalue() == ''
    app.extensions.pop('read_parallel')

    app.setup_extension('write_parallel')
    assert app.is_parallel_allowed('read') is False
    assert app.is_parallel_allowed('write') is True
    assert ("the write_parallel extension does not declare if it is safe "
            "for parallel reading, assuming it isn't - please ") in warning.getvalue()
    app.extensions.pop('write_parallel')
    warning.truncate(0)  # reset warnings

    app.setup_extension('read_serial')
    assert app.is_parallel_allowed('read') is False
    assert "the read_serial extension is not safe for parallel reading" in warning.getvalue()
    warning.truncate(0)  # reset warnings
    assert app.is_parallel_allowed('write') is True
    assert warning.getvalue() == ''
    app.extensions.pop('read_serial')

    app.setup_extension('write_serial')
    assert app.is_parallel_allowed('read') is False
    assert app.is_parallel_allowed('write') is False
    assert ("the write_serial extension does not declare if it is safe "
            "for parallel reading, assuming it isn't - please ") in warning.getvalue()
    app.extensions.pop('write_serial')
    warning.truncate(0)  # reset warnings


@pytest.mark.sphinx('dummy', testroot='root')
def test_build_specific(app):
    app.builder.build = Mock()
    filenames = [app.srcdir / 'index.txt',                      # normal
                 app.srcdir / 'images',                         # without suffix
                 app.srcdir / 'notfound.txt',                   # not found
                 app.srcdir / 'img.png',                        # unknown suffix
                 '/index.txt',                                  # external file
                 app.srcdir / 'subdir',                         # directory
                 app.srcdir / 'subdir/includes.txt',            # file on subdir
                 app.srcdir / 'subdir/../subdir/excluded.txt']  # not normalized
    app.build(False, filenames)

    expected = ['index', 'img.png', 'subdir/includes', 'subdir/excluded']
    app.builder.build.assert_called_with(expected,
                                         method='specific',
                                         summary='4 source files given on command line')
