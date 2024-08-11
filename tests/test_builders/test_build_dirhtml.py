"""Test dirhtml builder."""

import posixpath

import pytest

from sphinx.util.inventory import InventoryFile


@pytest.mark.sphinx('dirhtml', testroot='builder-dirhtml')
def test_dirhtml(app):
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

    # objects.inv (refs: #7095)
    with (app.outdir / 'objects.inv').open('rb') as f:
        invdata = InventoryFile.load(f, 'path/to', posixpath.join)

    assert 'index' in invdata.get('std:doc', {})
    assert invdata['std:doc']['index'] == ('Project name not set', '', 'path/to/', '-')

    assert 'foo/index' in invdata.get('std:doc', {})
    assert invdata['std:doc']['foo/index'] == (
        'Project name not set',
        '',
        'path/to/foo/',
        '-',
    )

    assert 'index' in invdata.get('std:label', {})
    assert invdata['std:label']['index'] == (
        'Project name not set',
        '',
        'path/to/#index',
        '-',
    )

    assert 'foo' in invdata.get('std:label', {})
    assert invdata['std:label']['foo'] == (
        'Project name not set',
        '',
        'path/to/foo/#foo',
        'foo/index',
    )
