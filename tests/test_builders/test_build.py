"""Test all builders."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from docutils import nodes

from sphinx.errors import SphinxError

from tests.utils import extract_element, extract_node

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

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
