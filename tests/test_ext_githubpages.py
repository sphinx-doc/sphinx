"""
    test_ext_githubpages
    ~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.githubpages extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

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
    assert (app.outdir / 'CNAME').read_text() == 'sphinx-doc.org'
