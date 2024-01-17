"""Test the Theme class."""

import os

import pytest

import sphinx.builders.html
from sphinx.theming import Theme, ThemeError


@pytest.mark.sphinx(
    testroot='theming',
    confoverrides={'html_theme': 'ziptheme',
                   'html_theme_options.testopt': 'foo'})
def test_theme_api(app, status, warning):
    cfg = app.config

    themes = ['basic', 'default', 'scrolls', 'agogo', 'sphinxdoc', 'haiku',
              'traditional', 'epub', 'nature', 'pyramid', 'bizstyle', 'classic', 'nonav',
              'test-theme', 'ziptheme', 'staticfiles', 'parent', 'child', 'alabaster']

    # test Theme class API
    assert set(app.registry.html_themes.keys()) == set(themes)
    assert app.registry.html_themes['test-theme'] == str(app.srcdir / 'test_theme' / 'test-theme')
    assert app.registry.html_themes['ziptheme'] == str(app.srcdir / 'ziptheme.zip')
    assert app.registry.html_themes['staticfiles'] == str(app.srcdir / 'test_theme' / 'staticfiles')

    # test Theme instance API
    theme = app.builder.theme
    assert theme.name == 'ziptheme'
    themedir = theme.themedir
    assert theme.base.name == 'basic'
    assert len(theme.get_theme_dirs()) == 2

    # direct setting
    assert theme.get_config('theme', 'stylesheet') == 'custom.css'
    # inherited setting
    assert theme.get_config('options', 'nosidebar') == 'false'
    # nonexisting setting
    assert theme.get_config('theme', 'foobar', 'def') == 'def'
    with pytest.raises(ThemeError):
        theme.get_config('theme', 'foobar')

    # options API

    options = theme.get_options({'nonexisting': 'foo'})
    assert 'nonexisting' not in options

    options = theme.get_options(cfg.html_theme_options)
    assert options['testopt'] == 'foo'
    assert options['nosidebar'] == 'false'

    # cleanup temp directories
    theme.cleanup()
    assert not os.path.exists(themedir)


def test_nonexistent_theme_conf(tmp_path):
    # Check that error occurs with a non-existent theme.conf
    # (https://github.com/sphinx-doc/sphinx/issues/11668)
    with pytest.raises(ThemeError):
        Theme('dummy', str(tmp_path), None)


@pytest.mark.sphinx(testroot='double-inheriting-theme')
def test_double_inheriting_theme(app, status, warning):
    assert app.builder.theme.name == 'base_theme2'
    app.build()  # => not raises TemplateNotFound


@pytest.mark.sphinx(testroot='theming',
                    confoverrides={'html_theme': 'child'})
def test_nested_zipped_theme(app, status, warning):
    assert app.builder.theme.name == 'child'
    app.build()  # => not raises TemplateNotFound


@pytest.mark.sphinx(testroot='theming',
                    confoverrides={'html_theme': 'staticfiles'})
def test_staticfiles(app, status, warning):
    app.build()
    assert (app.outdir / '_static' / 'staticimg.png').exists()
    assert (app.outdir / '_static' / 'statictmpl.html').exists()
    assert (app.outdir / '_static' / 'statictmpl.html').read_text(encoding='utf8') == (
        '<!-- testing static templates -->\n'
        '<html><project>Python</project></html>'
    )

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<meta name="testopt" content="optdefault" />' in result


@pytest.mark.sphinx(testroot='theming',
                    confoverrides={'html_theme': 'test-theme'})
def test_dark_style(app, monkeypatch):
    monkeypatch.setattr(sphinx.builders.html, '_file_checksum', lambda o, f: '')

    style = app.builder.dark_highlighter.formatter_args.get('style')
    assert style.__name__ == 'MonokaiStyle'

    app.build()
    assert (app.outdir / '_static' / 'pygments_dark.css').exists()

    css_file, properties = app.registry.css_files[0]
    assert css_file == 'pygments_dark.css'
    assert "media" in properties
    assert properties["media"] == '(prefers-color-scheme: dark)'

    assert sorted(f.filename for f in app.builder._css_files) == [
        '_static/classic.css',
        '_static/pygments.css',
        '_static/pygments_dark.css',
    ]

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<link rel="stylesheet" type="text/css" href="_static/pygments.css" />' in result
    assert ('<link id="pygments_dark_css" media="(prefers-color-scheme: dark)" '
            'rel="stylesheet" type="text/css" '
            'href="_static/pygments_dark.css" />') in result


@pytest.mark.sphinx(testroot='theming')
def test_theme_sidebars(app, status, warning):
    app.build()

    # test-theme specifies globaltoc and searchbox as default sidebars
    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<h3><a href="#">Table of Contents</a></h3>' in result
    assert '<h3>Related Topics</h3>' not in result
    assert '<h3>This Page</h3>' not in result
    assert '<h3 id="searchlabel">Quick search</h3>' in result
