import pytest


@pytest.mark.sphinx('html', testroot='theming')
def test_theme_options(app, status, warning):
    app.build()

    result = (app.outdir / '_static' / 'documentation_options.js').read_text(encoding='utf8')
    assert 'NAVIGATION_WITH_KEYS: false' in result
    assert 'ENABLE_SEARCH_SHORTCUTS: true' in result


@pytest.mark.sphinx('html', testroot='theming',
                    confoverrides={'html_theme_options.navigation_with_keys': True,
                                   'html_theme_options.enable_search_shortcuts': False})
def test_theme_options_with_override(app, status, warning):
    app.build()

    result = (app.outdir / '_static' / 'documentation_options.js').read_text(encoding='utf8')
    assert 'NAVIGATION_WITH_KEYS: true' in result
    assert 'ENABLE_SEARCH_SHORTCUTS: false' in result


@pytest.mark.sphinx('html', testroot='build-html-theme-having-multiple-stylesheets')
def test_theme_having_multiple_stylesheets(app):
    app.build()
    content = (app.outdir / 'index.html').read_text(encoding='utf-8')

    assert '<link rel="stylesheet" type="text/css" href="_static/mytheme.css" />' in content
    assert '<link rel="stylesheet" type="text/css" href="_static/extra.css" />' in content
