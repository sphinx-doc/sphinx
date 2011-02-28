# -*- coding: utf-8 -*-
"""
    test_theming
    ~~~~~~~~~~~~

    Test the Theme class.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import zipfile

from util import *

from sphinx.theming import Theme, ThemeError


@with_app(confoverrides={'html_theme': 'ziptheme',
                         'html_theme_options.testopt': 'foo'})
def test_theme_api(app):
    cfg = app.config

    # test Theme class API
    assert set(Theme.themes.keys()) == \
           set(['basic', 'default', 'scrolls', 'agogo', 'sphinxdoc', 'haiku',
                'traditional', 'testtheme', 'ziptheme', 'epub', 'nature',
                'pyramid'])
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
