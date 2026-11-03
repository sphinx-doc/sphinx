"""Test all builders."""

from __future__ import annotations

import pickle
import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx.environment import BuildEnvironment
from sphinx.errors import SphinxError

from tests.utils import extract_element, extract_node

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any, BinaryIO

    from sphinx.testing.util import SphinxTestApp


def test_root_doc_not_found(
    tmp_path: Path, make_app: Callable[..., SphinxTestApp]
) -> None:
    (tmp_path / 'conf.py').touch()
    assert [p.name for p in tmp_path.iterdir()] == ['conf.py']

    app = make_app('dummy', srcdir=tmp_path)
    with pytest.raises(SphinxError):
        app.build(force_all=True)  # no index.rst


@pytest.mark.sphinx('text', testroot='circular')
def test_circular_toctree(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    warnings = app.warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: sub <- index <- sub'
    ) in warnings
    assert (
        'circular toctree references detected, ignoring: index <- sub <- index'
    ) in warnings


@pytest.mark.sphinx('text', testroot='numbered-circular')
def test_numbered_circular_toctree(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    warnings = app.warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: sub <- index <- sub'
    ) in warnings
    assert (
        'circular toctree references detected, ignoring: index <- sub <- index'
    ) in warnings


@pytest.mark.sphinx('text', testroot='toctree-multiple-parents')
def test_multiple_parents_toctree(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (
        "document is referenced in multiple toctrees: ['bravo', 'delta'], selecting: delta <- charlie"
    ) in app.status.getvalue()


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx('dummy', testroot='images')
def test_image_glob(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    # index.rst
    doctree = app.env.get_doctree('index')
    assert isinstance(doctree[0], nodes.Element)

    assert isinstance(extract_node(doctree, 0, 1), nodes.image)
    assert extract_element(doctree, 0, 1)['candidates'] == {'*': 'rimg.png'}
    assert extract_element(doctree, 0, 1)['uri'] == 'rimg.png'

    assert isinstance(extract_node(doctree, 0, 2), nodes.figure)
    assert isinstance(extract_node(doctree, 0, 2, 0), nodes.image)
    assert extract_element(doctree, 0, 2, 0)['candidates'] == {'*': 'rimg.png'}
    assert extract_element(doctree, 0, 2, 0)['uri'] == 'rimg.png'

    assert isinstance(extract_node(doctree, 0, 3), nodes.image)
    assert extract_element(doctree, 0, 3)['candidates'] == {
        'application/pdf': 'img.pdf',
        'image/gif': 'img.gif',
        'image/png': 'img.png',
    }
    assert extract_element(doctree, 0, 3)['uri'] == 'img.*'

    assert isinstance(extract_node(doctree, 0, 4), nodes.figure)
    assert isinstance(extract_node(doctree, 0, 4, 0), nodes.image)
    assert extract_element(doctree, 0, 4, 0)['candidates'] == {
        'application/pdf': 'img.pdf',
        'image/gif': 'img.gif',
        'image/png': 'img.png',
    }
    assert extract_element(doctree, 0, 4, 0)['uri'] == 'img.*'

    # subdir/index.rst
    doctree = app.env.get_doctree('subdir/index')
    assert isinstance(doctree[0], nodes.Element)

    assert isinstance(extract_node(doctree, 0, 1), nodes.image)
    assert extract_element(doctree, 0, 1)['candidates'] == {'*': 'subdir/rimg.png'}
    assert extract_element(doctree, 0, 1)['uri'] == 'subdir/rimg.png'

    assert isinstance(extract_node(doctree, 0, 2), nodes.image)
    assert extract_element(doctree, 0, 2)['candidates'] == {
        'application/pdf': 'subdir/svgimg.pdf',
        'image/svg+xml': 'subdir/svgimg.svg',
    }
    assert extract_element(doctree, 0, 2)['uri'] == 'subdir/svgimg.*'

    assert isinstance(extract_node(doctree, 0, 3), nodes.figure)
    assert isinstance(extract_node(doctree, 0, 3, 0), nodes.image)
    assert extract_element(doctree, 0, 3, 0)['candidates'] == {
        'application/pdf': 'subdir/svgimg.pdf',
        'image/svg+xml': 'subdir/svgimg.svg',
    }
    assert extract_element(doctree, 0, 3, 0)['uri'] == 'subdir/svgimg.*'


class SerializationInterrupted(Exception):
    """Stop the writer after a partial pickle has been flushed."""


@pytest.mark.sphinx('dummy', testroot='basic', freshenv=True)
@pytest.mark.parametrize('cache_name', ['index.doctree', 'environment.pickle'])
@pytest.mark.parametrize('existing', [True, False])
@pytest.mark.parametrize('fail', [False, True])
def test_cache_pickle_publication(
    app: SphinxTestApp,
    monkeypatch: pytest.MonkeyPatch,
    cache_name: str,
    existing: bool,
    fail: bool,
) -> None:
    app.build(force_all=True)
    filename = app.doctreedir / cache_name
    previous = filename.read_bytes()
    previous_mode = stat.S_IMODE(filename.stat().st_mode)
    if not existing:
        filename.unlink()
    original_paths = set(app.doctreedir.rglob('*'))
    original_dump = pickle.dump
    checked = []

    def dump(value: Any, stream: BinaryIO, protocol: int) -> None:
        matches = (
            isinstance(value, BuildEnvironment)
            if cache_name == 'environment.pickle'
            else isinstance(value, nodes.document)
        )
        if not matches:
            original_dump(value, stream, protocol)
            return
        data = pickle.dumps(value, protocol)
        halfway = len(data) // 2
        stream.write(data[:halfway])
        stream.flush()
        # A reader runs after the first half has reached the filesystem,
        # before the writer has finished serializing the new cache entry.
        if existing:
            assert filename.read_bytes() == previous
            pickle.loads(filename.read_bytes())
        else:
            assert not filename.exists()
        checked.append(True)
        if fail:
            raise SerializationInterrupted
        stream.write(data[halfway:])

    monkeypatch.setattr(pickle, 'dump', dump)
    app.env.all_docs['index'] = 0
    if fail:
        with pytest.raises(SerializationInterrupted):
            app.build(force_all=True)
        if existing and cache_name != 'environment.pickle':
            assert filename.read_bytes() == previous
        else:
            assert not filename.exists()
        # Application.build deliberately invalidates the environment after an
        # exception, independently of how the cache entry was written.
        assert not (app.doctreedir / 'environment.pickle').exists()
    else:
        app.build(force_all=True)
        pickle.loads(filename.read_bytes())
        if existing:
            assert stat.S_IMODE(filename.stat().st_mode) == previous_mode
    assert checked == [True]
    expected_paths = original_paths | {filename}
    if fail:
        expected_paths.discard(app.doctreedir / 'environment.pickle')
        if not existing:
            expected_paths.discard(filename)
    assert set(app.doctreedir.rglob('*')) == expected_paths


@pytest.mark.sphinx('dummy', testroot='basic', freshenv=True)
@pytest.mark.parametrize('cache_name', ['index.doctree', 'environment.pickle'])
def test_cache_pickle_replace_failure(
    app: SphinxTestApp,
    monkeypatch: pytest.MonkeyPatch,
    cache_name: str,
) -> None:
    app.build(force_all=True)
    filename = app.doctreedir / cache_name
    previous = filename.read_bytes()
    original_paths = set(app.doctreedir.rglob('*'))
    original_replace = Path.replace
    checked = []

    def replace(source: Path, target: Path) -> Path:
        if target == filename:
            # Serialization is complete, but publishing the file fails.
            pickle.loads(source.read_bytes())
            assert filename.read_bytes() == previous
            checked.append(True)
            raise PermissionError
        return original_replace(source, target)

    monkeypatch.setattr(Path, 'replace', replace)
    app.env.all_docs['index'] = 0
    with pytest.raises(PermissionError):
        app.build(force_all=True)
    assert checked == [True]
    if cache_name == 'index.doctree':
        assert filename.read_bytes() == previous
    assert set(app.doctreedir.rglob('*')) == original_paths - {
        app.doctreedir / 'environment.pickle'
    }
