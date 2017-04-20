# -*- coding: utf-8 -*-
"""
    test_theming
    ~~~~~~~~~~~~

    Test the Theme class.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

import pytest

from sphinx.theming import ThemeError


@pytest.mark.sphinx(
    confoverrides={'html_theme': 'ziptheme',
                   'html_theme_options.testopt': 'foo'})
def test_theme_api(app, status, warning):
    cfg = app.config

    # test Theme class API
    assert set(app.html_themes.keys()) == \
        set(['basic', 'default', 'scrolls', 'agogo', 'sphinxdoc', 'haiku',
             'traditional', 'testtheme', 'ziptheme', 'epub', 'nature',
             'pyramid', 'bizstyle', 'classic', 'nonav'])
    assert app.html_themes['testtheme'] == app.srcdir / 'testtheme'
    assert app.html_themes['ziptheme'] == app.srcdir / 'ziptheme.zip'

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
    with pytest.raises(ThemeError):
        theme.get_options({'nonexisting': 'foo'})
    options = theme.get_options(cfg.html_theme_options)
    assert options['testopt'] == 'foo'
    assert options['nosidebar'] == 'false'

    # cleanup temp directories
    theme.cleanup()
    assert not os.path.exists(themedir)


@pytest.mark.sphinx(testroot='tocdepth')  # a minimal root
def test_js_source(app, status, warning):
    # Now sphinx provides non-minified JS files for jquery.js and underscore.js
    # to clarify the source of the minified files. see also #1434.
    # If you update the version of the JS file, please update the source of the
    # JS file and version number in this test.

    app.builder.build(['contents'])

    v = '3.1.0'
    msg = 'jquery.js version does not match to {v}'.format(v=v)
    jquery_min = (app.outdir / '_static' / 'jquery.js').text()
    assert 'jQuery v{v}'.format(v=v) in jquery_min, msg
    jquery_src = (app.outdir / '_static' / 'jquery-{v}.js'.format(v=v)).text()
    assert 'jQuery JavaScript Library v{v}'.format(v=v) in jquery_src, msg

    v = '1.3.1'
    msg = 'underscore.js version does not match to {v}'.format(v=v)
    underscore_min = (app.outdir / '_static' / 'underscore.js').text()
    assert 'Underscore.js {v}'.format(v=v) in underscore_min, msg
    underscore_src = (app.outdir / '_static' / 'underscore-{v}.js'.format(v=v)).text()
    assert 'Underscore.js {v}'.format(v=v) in underscore_src, msg


@pytest.mark.sphinx(testroot='double-inheriting-theme')
def test_double_inheriting_theme(app, status, warning):
    assert app.builder.theme.name == 'base_theme2'
    app.build()  # => not raises TemplateNotFound


@pytest.mark.sphinx(testroot='theming',
                    confoverrides={'html_theme': 'child'})
def test_nested_zipped_theme(app, status, warning):
    assert app.builder.theme.name == 'child'
    app.build()  # => not raises TemplateNotFound
