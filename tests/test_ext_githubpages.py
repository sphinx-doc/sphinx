"""Test sphinx.ext.githubpages extension."""

import pytest


@pytest.mark.sphinx('html', testroot='ext-githubpages')
def test_githubpages(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / '.nojekyll').exists()
    assert not (app.outdir / 'CNAME').exists()


@pytest.mark.sphinx('html', testroot='ext-githubpages',
                    confoverrides={'html_baseurl': 'https://sphinx-doc.github.io'})
def test_no_cname_for_github_io_domain(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / '.nojekyll').exists()
    assert not (app.outdir / 'CNAME').exists()


@pytest.mark.sphinx('html', testroot='ext-githubpages',
                    confoverrides={'html_baseurl': 'https://sphinx-doc.org'})
def test_cname_for_custom_domain(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / '.nojekyll').exists()
    assert (app.outdir / 'CNAME').read_text(encoding='utf8') == 'sphinx-doc.org'
