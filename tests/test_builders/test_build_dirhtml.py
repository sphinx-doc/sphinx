"""Test dirhtml builder."""

from __future__ import annotations

import posixpath
from typing import TYPE_CHECKING

import pytest

from sphinx.util.inventory import InventoryFile, _InventoryItem

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('dirhtml', testroot='builder-dirhtml')
def test_dirhtml(app: SphinxTestApp) -> None:
    app.build()

    assert (app.outdir / 'index.html').exists()
    assert (app.outdir / 'foo/index.html').exists()
    assert (app.outdir / 'foo/foo_1/index.html').exists()
    assert (app.outdir / 'foo/foo_2/index.html').exists()
    assert (app.outdir / 'bar/index.html').exists()

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert 'href="foo/"' in content
    assert 'href="foo/foo_1/"' in content
    assert 'href="foo/foo_2/"' in content
    assert 'href="bar/"' in content

    # objects.inv
    # See: https://github.com/sphinx-doc/sphinx/issues/7095
    with (app.outdir / 'objects.inv').open('rb') as f:
        invdata = InventoryFile.load(f, 'path/to', posixpath.join)

    assert 'index' in invdata.get('std:doc', {})
    assert invdata['std:doc']['index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/',
        display_name='-',
    )

    assert 'foo/index' in invdata.get('std:doc', {})
    assert invdata['std:doc']['foo/index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/foo/',
        display_name='-',
    )

    assert 'index' in invdata.get('std:label', {})
    assert invdata['std:label']['index'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/#index',
        display_name='-',
    )

    assert 'foo' in invdata.get('std:label', {})
    assert invdata['std:label']['foo'] == _InventoryItem(
        project_name='Project name not set',
        project_version='',
        uri='path/to/foo/#foo',
        display_name='foo/index',
    )
