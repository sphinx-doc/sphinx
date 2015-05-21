#!python
# -*- coding: utf-8 -*-
"""
    test_inherit_plugin_theme.py
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test inheriting the themes installed as plug-in.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from util import with_app
from path import path
import sphinx.theming

original_function = None

def patched_function():
    list_ = original_function()
    p = path(__file__ or '.')
    tpath = p.joinpath('../roots/test-inherit-plugin-theme/base_themes_dir')
    tpath = tpath.abspath()
    list_.append(tpath)
    return list_

def setup_module():
    global original_function
    original_function = sphinx.theming.load_theme_plugins
    sphinx.theming.load_theme_plugins = patched_function

@with_app(testroot='inherit-plugin-theme')
def test_inherit_plugin_theme(app, status, warning):
    app.builder.build_all()
