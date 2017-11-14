# -*- coding: utf-8 -*-
"""
    test_ext_viewcode
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.viewcode extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys

import pytest


@pytest.mark.sphinx(testroot='ext-viewcode')
def test_viewcode(app, status, warning, include_short_names=True):
    app.builder.build_all()

    warnings = re.sub(r'\\+', '/', warning.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include " +
        r"file .*/spam/__init__.py'",
        warnings
    )

    result = (app.outdir / 'index.html').text(encoding='utf-8')
    link_count = 2
    if not include_short_names:
        link_count = 1
    assert result.count('href="_modules/spam/mod1.html#func1"') == link_count
    assert result.count('href="_modules/spam/mod2.html#func2"') == link_count
    assert result.count('href="_modules/spam/mod1.html#Class1"') == link_count
    assert result.count('href="_modules/spam/mod2.html#Class2"') == link_count
    assert result.count('@decorator') == 1

    # test that the class attribute is correctly documented
    assert result.count('this is Class3') == 2
    assert 'this is the class attribute class_attr' in result
    # the next assert fails, until the autodoc bug gets fixed
    assert result.count('this is the class attribute class_attr') == 2


@pytest.mark.sphinx(testroot='ext-viewcode', tags=['test_linkcode'])
def test_linkcode(app, status, warning):
    app.builder.build(['objects'])

    stuff = (app.outdir / 'objects.html').text(encoding='utf-8')

    assert 'http://foobar/source/foolib.py' in stuff
    assert 'http://foobar/js/' in stuff
    assert 'http://foobar/c/' in stuff
    assert 'http://foobar/cpp/' in stuff


@pytest.mark.sphinx(testroot='ext-viewcode', tags=['test_source_files'])
def test_local_source_files(app, status, warning):
    # Let autodoc document the module,
    # but unload it so that viewcode has to use the source files.
    def unload_spam(app, doctree):
        sys.path.pop(0)
        for module in list(sys.modules):
            if module.startswith('spam.') or module == 'spam':
                del sys.modules[module]

    listeners = app.events.listeners['doctree-read']
    viewcode_read = listeners.popitem()[1]
    app.connect('doctree-read', unload_spam)
    app.connect('doctree-read', viewcode_read)

    test_viewcode(app, status, warning, include_short_names=False)
