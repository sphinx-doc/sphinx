"""Test the Theme class."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING
from xml.etree.ElementTree import ParseError

import pytest
from defusedxml.ElementTree import parse as xml_parse

import sphinx.builders.html
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.errors import ThemeError
from sphinx.theming import (
    _ConfigFile,
    _convert_theme_conf,
    _convert_theme_toml,
    _load_theme,
    _load_theme_conf,
    _load_theme_toml,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.testing.util import SphinxTestApp

HERE = Path(__file__).resolve().parent


@pytest.mark.sphinx(
    'html',
    testroot='theming',
    confoverrides={'html_theme': 'ziptheme', 'html_theme_options.testopt': 'foo'},
)
def test_theme_api(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    themes = [
        'basic',
        'default',
        'scrolls',
        'agogo',
        'sphinxdoc',
        'haiku',
        'traditional',
        'epub',
        'nature',
        'pyramid',
        'bizstyle',
        'classic',
        'nonav',
        'test-theme',
        'ziptheme',
        'staticfiles',
        'parent',
        'child',
        'alabaster',
    ]

    # test Theme class API
    assert set(app.registry.html_themes.keys()) == set(themes)
    assert app.registry.html_themes['test-theme'] == (
        app.srcdir / 'test_theme' / 'test-theme'
    )
    assert app.registry.html_themes['ziptheme'] == (app.srcdir / 'ziptheme.zip')
    assert app.registry.html_themes['staticfiles'] == (
        app.srcdir / 'test_theme' / 'staticfiles'
    )

    # test Theme instance API
    theme = app.builder.theme
    assert theme.name == 'ziptheme'
    assert len(theme.get_theme_dirs()) == 2

    # direct setting
    assert theme.get_config('theme', 'stylesheet') == 'custom.css'
    # inherited setting
    assert theme.get_config('options', 'nosidebar') == 'false'
    # nonexisting setting
    assert theme.get_config('theme', 'foobar', 'def') == 'def'
    with pytest.raises(ThemeError):
        theme.get_config('theme', 'foobar')
    # nonexisting section
    with pytest.raises(ThemeError):
        theme.get_config('foobar', 'foobar')

    # options API

    options = theme.get_options({'nonexisting': 'foo'})
    assert 'nonexisting' not in options

    options = theme.get_options(app.config.html_theme_options)
    assert options['testopt'] == 'foo'
    assert options['nosidebar'] == 'false'

    # cleanup temp directories
    theme._cleanup()
    assert not any(p.exists() for p in theme._tmp_dirs)


def test_nonexistent_theme_settings(tmp_path: Path) -> None:
    # Check that error occurs with a non-existent theme.toml or theme.conf
    # https://github.com/sphinx-doc/sphinx/issues/11668
    with pytest.raises(ThemeError):
        _load_theme('', tmp_path)


@pytest.mark.sphinx('html', testroot='double-inheriting-theme')
def test_double_inheriting_theme(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.theme.name == 'base_theme2'
    app.build()  # => not raises TemplateNotFound


@pytest.mark.sphinx(
    'html',
    testroot='theming',
    confoverrides={'html_theme': 'child'},
)
def test_nested_zipped_theme(app: SphinxTestApp) -> None:
    assert isinstance(app.builder, StandaloneHTMLBuilder)  # type-checking
    assert app.builder.theme.name == 'child'
    app.build()  # => not raises TemplateNotFound


@pytest.mark.sphinx(
    'html',
    testroot='theming',
    confoverrides={'html_theme': 'staticfiles'},
)
def test_staticfiles(app: SphinxTestApp) -> None:
    app.build()
    assert (app.outdir / '_static' / 'legacytmpl.html').exists()
    assert (app.outdir / '_static' / 'legacytmpl.html').read_text(encoding='utf8') == (
        '<!-- testing legacy _t static templates -->\n'
        '<html><project>project name not set</project></html>'
    )
    assert (app.outdir / '_static' / 'staticimg.png').exists()
    assert (app.outdir / '_static' / 'statictmpl.html').exists()
    assert (app.outdir / '_static' / 'statictmpl.html').read_text(encoding='utf8') == (
        '<!-- testing static templates -->\n<html><project>Project name not set</project></html>'
    )

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<meta name="testopt" content="optdefault" />' in result


@pytest.mark.sphinx(
    'html',
    testroot='theming',
    confoverrides={'html_theme': 'test-theme'},
)
def test_dark_style(app: SphinxTestApp, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sphinx.builders.html, '_file_checksum', lambda o, f: '')

    assert isinstance(app.builder, StandaloneHTMLBuilder)
    assert app.builder.dark_highlighter is not None
    style = app.builder.dark_highlighter.formatter_args['style']
    assert style.__name__ == 'MonokaiStyle'

    app.build()
    assert (app.outdir / '_static' / 'pygments_dark.css').exists()

    css_file = app.builder._css_files[1]
    assert css_file.filename == '_static/pygments_dark.css'
    assert 'media' in css_file.attributes
    assert css_file.attributes['media'] == '(prefers-color-scheme: dark)'

    assert sorted(str(f.filename) for f in app.builder._css_files) == [
        '_static/classic.css',
        '_static/pygments.css',
        '_static/pygments_dark.css',
    ]

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<link rel="stylesheet" type="text/css" href="_static/pygments.css" />'
    ) in result
    assert (
        '<link id="pygments_dark_css" media="(prefers-color-scheme: dark)" '
        'rel="stylesheet" type="text/css" '
        'href="_static/pygments_dark.css" />'
    ) in result


@pytest.mark.sphinx('html', testroot='theming')
def test_theme_sidebars(app: SphinxTestApp) -> None:
    app.build()

    # test-theme specifies globaltoc and searchbox as default sidebars
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<h3><a href="#">Table of Contents</a></h3>' in result
    assert '<h3>Related Topics</h3>' not in result
    assert '<h3>This Page</h3>' not in result
    assert '<h3 id="searchlabel">Quick search</h3>' in result


@pytest.mark.parametrize(
    'theme_name',
    [
        'alabaster',
        'agogo',
        'basic',
        'bizstyle',
        'classic',
        'default',
        'epub',
        'haiku',
        'nature',
        'nonav',
        'pyramid',
        'scrolls',
        'sphinxdoc',
        'traditional',
    ],
)
def test_theme_builds(
    make_app: Callable[..., SphinxTestApp],
    rootdir: Path,
    sphinx_test_tempdir: Path,
    theme_name: str,
) -> None:
    """Test all the themes included with Sphinx build a simple project and produce valid XML."""
    testroot_path = rootdir / 'test-basic'
    srcdir = sphinx_test_tempdir / f'test-theme-{theme_name}'
    shutil.copytree(testroot_path, srcdir)

    app = make_app(srcdir=srcdir, confoverrides={'html_theme': theme_name})
    app.build()
    assert not app.warning.getvalue().strip()
    assert app.outdir.joinpath('index.html').exists()

    # check that the generated HTML files are well-formed (as strict XML)
    for html_file in app.outdir.rglob('*.html'):
        try:
            xml_parse(html_file)
        except ParseError as exc:
            pytest.fail(f'Failed to parse {html_file.relative_to(app.outdir)}: {exc}')


def test_config_file_toml() -> None:
    config_path = HERE / 'theme.toml'
    cfg = _load_theme_toml(config_path)
    config = _convert_theme_toml(cfg)

    assert config == _ConfigFile(
        stylesheets=('spam.css', 'ham.css'),
        sidebar_templates=None,
        pygments_style_default='spam',
        pygments_style_dark=None,
        options={'lobster': 'thermidor'},
    )


def test_config_file_conf() -> None:
    config_path = HERE / 'theme.conf'
    cfg = _load_theme_conf(config_path)
    config = _convert_theme_conf(cfg)

    assert config == _ConfigFile(
        stylesheets=('spam.css', 'ham.css'),
        sidebar_templates=None,
        pygments_style_default='spam',
        pygments_style_dark=None,
        options={'lobster': 'thermidor'},
    )
