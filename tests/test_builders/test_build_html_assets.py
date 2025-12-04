"""Test the HTML builder and check output against XPath."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

import sphinx.builders.html
from sphinx.builders.html._assets import _file_checksum
from sphinx.errors import ThemeError

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='html_assets')
def test_html_assets(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    # exclude_path and its family
    assert not (app.outdir / 'static' / 'index.html').exists()
    assert not (app.outdir / 'extra' / 'index.html').exists()

    # html_static_path
    assert not (app.outdir / '_static' / '.htaccess').exists()
    assert not (app.outdir / '_static' / '.htpasswd').exists()
    assert (app.outdir / '_static' / 'API.html').exists()
    assert (app.outdir / '_static' / 'API.html').read_text(
        encoding='utf8'
    ) == 'Sphinx-1.4.4'
    assert (app.outdir / '_static' / 'css' / 'style.css').exists()
    assert (app.outdir / '_static' / 'js' / 'custom.js').exists()
    assert (app.outdir / '_static' / 'rimg.png').exists()
    assert not (app.outdir / '_static' / '_build' / 'index.html').exists()
    assert (app.outdir / '_static' / 'background.png').exists()
    assert not (app.outdir / '_static' / 'subdir' / '.htaccess').exists()
    assert not (app.outdir / '_static' / 'subdir' / '.htpasswd').exists()

    # html_extra_path
    assert (app.outdir / '.htaccess').exists()
    assert not (app.outdir / '.htpasswd').exists()
    assert (app.outdir / 'API.html.jinja').exists()
    assert (app.outdir / 'css/style.css').exists()
    assert (app.outdir / 'rimg.png').exists()
    assert not (app.outdir / '_build' / 'index.html').exists()
    assert (app.outdir / 'background.png').exists()
    assert (app.outdir / 'subdir' / '.htaccess').exists()
    assert not (app.outdir / 'subdir' / '.htpasswd').exists()

    # html_css_files
    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<link rel="stylesheet" type="text/css" href="_static/css/style.css" />'
    ) in content
    assert (
        '<link media="print" rel="stylesheet" title="title" type="text/css" '
        'href="https://example.com/custom.css" />'
    ) in content

    # html_js_files
    assert '<script src="_static/js/custom.js"></script>' in content
    assert (
        '<script async="async" src="https://example.com/script.js"></script>'
    ) in content


@pytest.mark.sphinx('html', testroot='html_assets')
def test_assets_order(app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sphinx.builders.html, '_file_checksum', lambda o, f: '')

    app.add_css_file('normal.css')
    app.add_css_file('early.css', priority=100)
    app.add_css_file('late.css', priority=750)
    app.add_css_file('lazy.css', priority=900)
    app.add_js_file('normal.js')
    app.add_js_file('early.js', priority=100)
    app.add_js_file('late.js', priority=750)
    app.add_js_file('lazy.js', priority=900)

    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # css_files
    expected = [
        '_static/early.css',
        '_static/pygments.css',
        'https://example.com/custom.css',
        '_static/normal.css',
        '_static/late.css',
        '_static/css/style.css',
        '_static/lazy.css',
    ]
    pattern = '.*'.join(f'href="{re.escape(f)}"' for f in expected)
    assert re.search(pattern, content, re.DOTALL), content

    # js_files
    expected = [
        '_static/early.js',
        '_static/doctools.js',
        '_static/sphinx_highlight.js',
        'https://example.com/script.js',
        '_static/normal.js',
        '_static/late.js',
        '_static/js/custom.js',
        '_static/lazy.js',
    ]
    pattern = '.*'.join(f'src="{re.escape(f)}"' for f in expected)
    assert re.search(pattern, content, re.DOTALL), content


@pytest.mark.sphinx('html', testroot='html_file_checksum')
def test_file_checksum(app: SphinxTestApp) -> None:
    app.add_css_file('stylesheet-a.css')
    app.add_css_file('stylesheet-b.css')
    app.add_css_file('https://example.com/custom.css')
    app.add_js_file('script.js')
    app.add_js_file('empty.js')
    app.add_js_file('https://example.com/script.js')

    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # checksum for local files
    assert (
        '<link rel="stylesheet" type="text/css" href="_static/stylesheet-a.css?v=e575b6df" />'
    ) in content
    assert (
        '<link rel="stylesheet" type="text/css" href="_static/stylesheet-b.css?v=a2d5cc0f" />'
    ) in content
    assert '<script src="_static/script.js?v=48278d48"></script>' in content

    # empty files have no checksum
    assert '<script src="_static/empty.js"></script>' in content

    # no checksum for hyperlinks
    assert (
        '<link rel="stylesheet" type="text/css" href="https://example.com/custom.css" />'
    ) in content
    assert '<script src="https://example.com/script.js"></script>' in content


def test_file_checksum_query_string() -> None:
    with pytest.raises(
        ThemeError,
        match='Local asset file paths must not contain query strings',
    ):
        _file_checksum(Path(), 'with_query_string.css?dead_parrots=1')

    with pytest.raises(
        ThemeError,
        match='Local asset file paths must not contain query strings',
    ):
        _file_checksum(Path(), 'with_query_string.js?dead_parrots=1')

    with pytest.raises(
        ThemeError,
        match='Local asset file paths must not contain query strings',
    ):
        _file_checksum(Path.cwd(), '_static/with_query_string.css?dead_parrots=1')

    with pytest.raises(
        ThemeError,
        match='Local asset file paths must not contain query strings',
    ):
        _file_checksum(Path.cwd(), '_static/with_query_string.js?dead_parrots=1')


@pytest.mark.sphinx('html', testroot='html_assets')
def test_javscript_loading_method(app: SphinxTestApp) -> None:
    app.add_js_file('normal.js')
    app.add_js_file('early.js', loading_method='async')
    app.add_js_file('late.js', loading_method='defer')

    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    assert '<script src="_static/normal.js"></script>' in content
    assert '<script async="async" src="_static/early.js"></script>' in content
    assert '<script defer="defer" src="_static/late.js"></script>' in content
