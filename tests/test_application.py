"""Test the Sphinx class."""

from __future__ import annotations

import shutil
import sys
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from docutils import nodes

import sphinx.application
from sphinx.errors import ExtensionError
from sphinx.testing.util import SphinxTestApp
from sphinx.util import logging
from sphinx.util.console import strip_colors

if TYPE_CHECKING:
    import os


def test_instantiation(
    tmp_path_factory: pytest.TempPathFactory,
    rootdir: str | os.PathLike[str] | None,
) -> None:
    # Given
    src_dir = tmp_path_factory.getbasetemp() / 'root'

    # special support for sphinx/tests
    if rootdir and not src_dir.exists():
        shutil.copytree(Path(str(rootdir)) / 'test-root', src_dir)

    saved_path = sys.path.copy()

    # When
    app_ = SphinxTestApp(
        srcdir=src_dir,
        status=StringIO(),
        warning=StringIO(),
    )
    sys.path[:] = saved_path
    app_.cleanup()

    # Then
    assert isinstance(app_, sphinx.application.Sphinx)


@pytest.mark.sphinx('html', testroot='root')
def test_events(app):
    def empty():
        pass

    with pytest.raises(ExtensionError) as excinfo:
        app.connect('invalid', empty)
    assert 'Unknown event name: invalid' in str(excinfo.value)

    app.add_event('my_event')
    with pytest.raises(ExtensionError) as excinfo:
        app.add_event('my_event')
    assert "Event 'my_event' already present" in str(excinfo.value)

    def mock_callback(a_app, *args):
        assert a_app is app
        assert emit_args == args
        return 'ret'

    emit_args = (1, 3, 'string')
    listener_id = app.connect('my_event', mock_callback)
    assert app.emit('my_event', *emit_args) == ['ret'], 'Callback not called'

    app.disconnect(listener_id)
    assert app.emit('my_event', *emit_args) == [], 'Callback called when disconnected'


@pytest.mark.sphinx('html', testroot='root')
def test_emit_with_nonascii_name_node(app):
    node = nodes.section(names=['\u65e5\u672c\u8a9e'])
    app.emit('my_event', node)


@pytest.mark.sphinx('html', testroot='root')
def test_extensions(app):
    app.setup_extension('shutil')
    warning = strip_colors(app.warning.getvalue())
    assert "extension 'shutil' has no setup() function" in warning


@pytest.mark.sphinx('html', testroot='root')
def test_extension_in_blacklist(app):
    app.setup_extension('sphinxjp.themecore')
    msg = strip_colors(app.warning.getvalue())
    assert msg.startswith("WARNING: the extension 'sphinxjp.themecore' was")


@pytest.mark.sphinx('html', testroot='add_source_parser')
def test_add_source_parser(app):
    assert set(app.config.source_suffix) == {'.rst', '.test'}

    # .rst; only in :confval:`source_suffix`
    assert '.rst' not in app.registry.get_source_parsers()
    assert app.registry.source_suffix['.rst'] == 'restructuredtext'

    # .test; configured by API
    assert app.registry.source_suffix['.test'] == 'test'
    assert 'test' in app.registry.get_source_parsers()
    assert app.registry.get_source_parsers()['test'].__name__ == 'TestSourceParser'


@pytest.mark.sphinx('html', testroot='extensions')
def test_add_is_parallel_allowed(app):
    logging.setup(app, app.status, app.warning)

    assert app.is_parallel_allowed('read') is True
    assert app.is_parallel_allowed('write') is True
    assert app.warning.getvalue() == ''

    app.setup_extension('read_parallel')
    assert app.is_parallel_allowed('read') is True
    assert app.is_parallel_allowed('write') is True
    assert app.warning.getvalue() == ''
    app.extensions.pop('read_parallel')

    app.setup_extension('write_parallel')
    assert app.is_parallel_allowed('read') is False
    assert app.is_parallel_allowed('write') is True
    assert (
        'the write_parallel extension does not declare if it is safe '
        "for parallel reading, assuming it isn't - please "
    ) in app.warning.getvalue()
    app.extensions.pop('write_parallel')
    app.warning.truncate(0)  # reset warnings

    app.setup_extension('read_serial')
    assert app.is_parallel_allowed('read') is False
    assert (
        'the read_serial extension is not safe for parallel reading'
    ) in app.warning.getvalue()
    app.warning.truncate(0)  # reset warnings
    assert app.is_parallel_allowed('write') is True
    assert app.warning.getvalue() == ''
    app.extensions.pop('read_serial')

    app.setup_extension('write_serial')
    assert app.is_parallel_allowed('read') is False
    assert app.is_parallel_allowed('write') is False
    assert (
        'the write_serial extension does not declare if it is safe '
        "for parallel reading, assuming it isn't - please "
    ) in app.warning.getvalue()
    app.extensions.pop('write_serial')
    app.warning.truncate(0)  # reset warnings


@pytest.mark.sphinx('dummy', testroot='root')
def test_build_specific(app):
    app.builder.build = Mock()
    filenames = [
        app.srcdir / 'index.txt',                      # normal
        app.srcdir / 'images',                         # without suffix
        app.srcdir / 'notfound.txt',                   # not found
        app.srcdir / 'img.png',                        # unknown suffix
        '/index.txt',                                  # external file
        app.srcdir / 'subdir',                         # directory
        app.srcdir / 'subdir/includes.txt',            # file on subdir
        app.srcdir / 'subdir/../subdir/excluded.txt',  # not normalized
    ]  # fmt: skip
    app.build(False, filenames)

    expected = ['index', 'subdir/includes', 'subdir/excluded']
    app.builder.build.assert_called_with(
        expected,
        method='specific',
        summary='3 source files given on command line',
    )
