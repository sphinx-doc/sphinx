"""
    test_build_dirhtml
    ~~~~~~~~~~~~~~~~~~

    Test dirhtml builder.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import posixpath

import pytest

from sphinx.util.inventory import InventoryFile


@pytest.mark.sphinx(buildername='dirhtml', testroot='builder-dirhtml')
def test_dirhtml(app, status, warning):
    app.build()

    assert (app.outdir / 'index.html').exists()
    assert (app.outdir / 'foo/index.html').exists()
    assert (app.outdir / 'foo/foo_1/index.html').exists()
    assert (app.outdir / 'foo/foo_2/index.html').exists()
    assert (app.outdir / 'bar/index.html').exists()

    content = (app.outdir / 'index.html').read_text()
    assert 'href="foo/"' in content
    assert 'href="foo/foo_1/"' in content
    assert 'href="foo/foo_2/"' in content
    assert 'href="bar/"' in content

    # objects.inv (refs: #7095)
    with (app.outdir / 'objects.inv').open('rb') as f:
        invdata = InventoryFile.load(f, 'path/to', posixpath.join)

    assert 'index' in invdata.get('std:doc')
    assert ('Python', '', 'path/to/', '-') == invdata['std:doc']['index']

    assert 'foo/index' in invdata.get('std:doc')
    assert ('Python', '', 'path/to/foo/', '-') == invdata['std:doc']['foo/index']

    assert 'index' in invdata.get('std:label')
    assert ('Python', '', 'path/to/#index', '-') == invdata['std:label']['index']

    assert 'foo' in invdata.get('std:label')
    assert ('Python', '', 'path/to/foo/#foo', 'foo/index') == invdata['std:label']['foo']
