# -*- coding: utf-8 -*-
"""
    test_ext_viewcode
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.viewcode extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx(testroot='ext-viewcode')
def test_viewcode(app, status, warning):
    app.builder.build_all()

    warnings = re.sub(r'\\+', '/', warning.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include " +
        r"file .*/spam/__init__.py'",
        warnings
    )

    result = (app.outdir / 'index.html').text(encoding='utf-8')
    assert result.count('href="_modules/spam/mod1.html#func1"') == 2
    assert result.count('href="_modules/spam/mod2.html#func2"') == 2
    assert result.count('href="_modules/spam/mod1.html#Class1"') == 2
    assert result.count('href="_modules/spam/mod2.html#Class2"') == 2
    assert result.count('@decorator') == 1

    # test that the class attribute is correctly documented
    assert result.count('this is Class3') == 2
    assert 'this is the class attribute class_attr' in result
    # the next assert fails, until the autodoc bug gets fixed
    assert result.count('this is the class attribute class_attr') == 2

    result = (app.outdir / '_modules/spam/mod1.html').text(encoding='utf-8')
    result = re.sub('<span class=".*?">', '<span>', result)  # filter pygments classes
    assert ('<div class="viewcode-block" id="Class1"><a class="viewcode-back" '
            'href="../../index.html#spam.Class1">[docs]</a>'
            '<span>@decorator</span>\n'
            '<span>class</span> <span>Class1</span>'
            '<span>(</span><span>object</span><span>):</span>\n'
            '    <span>&quot;&quot;&quot;</span>\n'
            '<span>    this is Class1</span>\n'
            '<span>    &quot;&quot;&quot;</span></div>\n') in result


@pytest.mark.sphinx(testroot='ext-viewcode', tags=['test_linkcode'])
def test_linkcode(app, status, warning):
    app.builder.build(['objects'])

    stuff = (app.outdir / 'objects.html').text(encoding='utf-8')

    assert 'http://foobar/source/foolib.py' in stuff
    assert 'http://foobar/js/' in stuff
    assert 'http://foobar/c/' in stuff
    assert 'http://foobar/cpp/' in stuff


@pytest.mark.sphinx(testroot='ext-viewcode-find')
def test_local_source_files(app, status, warning):
    def find_source(app, modname):
        if modname == 'not_a_package':
            source = (app.srcdir / 'not_a_package/__init__.py').text()
            tags = {
                'func1': ('def', 3, 3),
                'Class1': ('class', 3, 3),
                'not_a_package.submodule.func1': ('def', 3, 3),
                'not_a_package.submodule.Class1': ('class', 3, 3),
            }
        else:
            source = (app.srcdir / 'not_a_package/submodule.py').text()
            tags = {
                'not_a_package.submodule.func1': ('def', 11, 15),
                'Class1': ('class', 19, 22),
                'not_a_package.submodule.Class1': ('class', 19, 22),
                'Class3': ('class', 25, 30),
                'not_a_package.submodule.Class3.class_attr': ('other', 29, 29),
            }
        return (source, tags)

    app.connect('viewcode-find-source', find_source)
    app.builder.build_all()

    warnings = re.sub(r'\\+', '/', warning.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include " +
        r"file .*/not_a_package/__init__.py'",
        warnings
    )

    result = (app.outdir / 'index.html').text(encoding='utf-8')
    assert result.count('href="_modules/not_a_package.html#func1"') == 1
    assert result.count('href="_modules/not_a_package.html#not_a_package.submodule.func1"') == 1
    assert result.count('href="_modules/not_a_package/submodule.html#Class1"') == 1
    assert result.count('href="_modules/not_a_package/submodule.html#Class3"') == 1
    assert result.count('href="_modules/not_a_package/submodule.html#not_a_package.submodule.Class1"') == 1

    assert result.count('href="_modules/not_a_package/submodule.html#not_a_package.submodule.Class3.class_attr"') == 1
    assert result.count('This is the class attribute class_attr') == 1
