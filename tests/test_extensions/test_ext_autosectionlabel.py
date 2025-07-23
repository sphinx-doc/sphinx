"""Test sphinx.ext.autosectionlabel extension."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel')
def test_autosectionlabel_html(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    html = (
        '<li><p><a class="reference internal" href="#introduce-of-sphinx">'
        '<span class=".*?">Introduce of Sphinx</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#installation">'
        '<span class="std std-ref">Installation</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#for-windows-users">'
        '<span class="std std-ref">For Windows users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#for-unix-users">'
        '<span class="std std-ref">For UNIX users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#linux">'
        '<span class="std std-ref">Linux</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    html = (
        '<li><p><a class="reference internal" href="#freebsd">'
        '<span class="std std-ref">FreeBSD</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # for smart_quotes
    # See: https://github.com/sphinx-doc/sphinx/issues/4027
    html = (
        '<li><p><a class="reference internal" '
        'href="#this-one-s-got-an-apostrophe">'
        '<span class="std std-ref">This one’s got an apostrophe'
        '</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)


# Reuse test definition from above, just change the test root directory
@pytest.mark.sphinx('html', testroot='ext-autosectionlabel-prefix-document')
def test_autosectionlabel_prefix_document_html(app: SphinxTestApp) -> None:
    test_autosectionlabel_html(app)


@pytest.mark.sphinx(
    'html',
    testroot='ext-autosectionlabel',
    confoverrides={'autosectionlabel_maxdepth': 3},
)
def test_autosectionlabel_maxdepth(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # depth: 1
    html = (
        '<li><p><a class="reference internal" href="#test-ext-autosectionlabel">'
        '<span class=".*?">test-ext-autosectionlabel</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # depth: 2
    html = (
        '<li><p><a class="reference internal" href="#installation">'
        '<span class="std std-ref">Installation</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # depth: 3
    html = (
        '<li><p><a class="reference internal" href="#for-windows-users">'
        '<span class="std std-ref">For Windows users</span></a></p></li>'
    )
    assert re.search(html, content, re.DOTALL)

    # depth: 4
    html = '<li><p><span class="xref std std-ref">Linux</span></p></li>'
    assert re.search(html, content, re.DOTALL)

    assert "WARNING: undefined label: 'linux'" in app.warning.getvalue()
