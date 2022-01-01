"""
    test_ext_autosectionlabel
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.autosectionlabel extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel')
def test_autosectionlabel_html(app, status, warning, skipped_labels=False):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    html = ('<li><p><a class="reference internal" href="#introduce-of-sphinx">'
            '<span class=".*?">Introduce of Sphinx</span></a></p></li>')
    assert re.search(html, content, re.S)

    html = ('<li><p><a class="reference internal" href="#installation">'
            '<span class="std std-ref">Installation</span></a></p></li>')
    assert re.search(html, content, re.S)

    html = ('<li><p><a class="reference internal" href="#for-windows-users">'
            '<span class="std std-ref">For Windows users</span></a></p></li>')
    assert re.search(html, content, re.S)

    html = ('<li><p><a class="reference internal" href="#for-unix-users">'
            '<span class="std std-ref">For UNIX users</span></a></p></li>')
    assert re.search(html, content, re.S)

    html = ('<li><p><a class="reference internal" href="#linux">'
            '<span class="std std-ref">Linux</span></a></p></li>')
    assert re.search(html, content, re.S)

    html = ('<li><p><a class="reference internal" href="#freebsd">'
            '<span class="std std-ref">FreeBSD</span></a></p></li>')
    assert re.search(html, content, re.S)

    # for smart_quotes (refs: #4027)
    html = ('<li><p><a class="reference internal" '
            'href="#this-one-s-got-an-apostrophe">'
            '<span class="std std-ref">This one’s got an apostrophe'
            '</span></a></p></li>')
    assert re.search(html, content, re.S)


# Re-use test definition from above, just change the test root directory
@pytest.mark.sphinx('html', testroot='ext-autosectionlabel-prefix-document')
def test_autosectionlabel_prefix_document_html(app, status, warning):
    test_autosectionlabel_html(app, status, warning)


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel',
                    confoverrides={'autosectionlabel_maxdepth': 3})
def test_autosectionlabel_maxdepth(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()

    # depth: 1
    html = ('<li><p><a class="reference internal" href="#test-ext-autosectionlabel">'
            '<span class=".*?">test-ext-autosectionlabel</span></a></p></li>')
    assert re.search(html, content, re.S)

    # depth: 2
    html = ('<li><p><a class="reference internal" href="#installation">'
            '<span class="std std-ref">Installation</span></a></p></li>')
    assert re.search(html, content, re.S)

    # depth: 3
    html = ('<li><p><a class="reference internal" href="#for-windows-users">'
            '<span class="std std-ref">For Windows users</span></a></p></li>')
    assert re.search(html, content, re.S)

    # depth: 4
    html = '<li><p><span class="xref std std-ref">Linux</span></p></li>'
    assert re.search(html, content, re.S)

    assert 'WARNING: undefined label: linux' in warning.getvalue()
