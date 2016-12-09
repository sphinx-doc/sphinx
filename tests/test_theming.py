# -*- coding: utf-8 -*-
"""
    test_theming
    ~~~~~~~~~~~~

    Test the Theme class.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import zipfile

import mock

from sphinx.theming import Theme, ThemeError

from util import with_app, raises, path


@with_app(confoverrides={'html_theme': 'ziptheme',
                         'html_theme_options.testopt': 'foo'})
def test_theme_api(app, status, warning):
    cfg = app.config

    # test Theme class API
    assert set(Theme.themes.keys()) == \
        set(['basic', 'default', 'scrolls', 'agogo', 'sphinxdoc', 'haiku',
             'traditional', 'testtheme', 'ziptheme', 'epub', 'nature',
             'pyramid', 'bizstyle', 'classic', 'nonav'])
    assert Theme.themes['testtheme'][1] is None
    assert isinstance(Theme.themes['ziptheme'][1], zipfile.ZipFile)

    # test Theme instance API
    theme = app.builder.theme
    assert theme.name == 'ziptheme'
    assert theme.themedir_created
    themedir = theme.themedir
    assert theme.base.name == 'basic'
    assert len(theme.get_dirchain()) == 2

    # direct setting
    assert theme.get_confstr('theme', 'stylesheet') == 'custom.css'
    # inherited setting
    assert theme.get_confstr('options', 'nosidebar') == 'false'
    # nonexisting setting
    assert theme.get_confstr('theme', 'foobar', 'def') == 'def'
    raises(ThemeError, theme.get_confstr, 'theme', 'foobar')

    # options API
    raises(ThemeError, theme.get_options, {'nonexisting': 'foo'})
    options = theme.get_options(cfg.html_theme_options)
    assert options['testopt'] == 'foo'
    assert options['nosidebar'] == 'false'

    # cleanup temp directories
    theme.cleanup()
    assert not os.path.exists(themedir)


@with_app(testroot='tocdepth')  # a minimal root
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


def test_double_inheriting_theme():
    from sphinx.theming import load_theme_plugins  # load original before patching

    def load_themes():
        roots = path(__file__).abspath().parent / 'roots'
        yield roots / 'test-double-inheriting-theme' / 'base_themes_dir'
        for t in load_theme_plugins():
            yield t

    @mock.patch('sphinx.theming.load_theme_plugins', side_effect=load_themes)
    @with_app(testroot='double-inheriting-theme')
    def test_double_inheriting_theme_(app, status, warning, m_):
        pass
    yield test_double_inheriting_theme_
