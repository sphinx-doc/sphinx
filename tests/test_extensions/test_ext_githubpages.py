"""Test sphinx.ext.githubpages extension."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import SphinxTestApp

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-githubpages')
def test_githubpages(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / '.nojekyll').exists()
    assert not (app.outdir / 'CNAME').exists()


@pytest.mark.sphinx(
    'html',
    testroot='ext-githubpages',
    confoverrides={'html_baseurl': 'https://sphinx-doc.github.io'},
)
def test_no_cname_for_github_io_domain(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / '.nojekyll').exists()
    assert not (app.outdir / 'CNAME').exists()


@pytest.mark.sphinx(
    'html',
    testroot='ext-githubpages',
    confoverrides={'html_baseurl': 'https://sphinx-doc.org'},
)
def test_cname_for_custom_domain(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    assert (app.outdir / '.nojekyll').exists()
    assert (app.outdir / 'CNAME').read_text(encoding='utf8') == 'sphinx-doc.org'
