"""Test sphinx.ext.viewcode extension."""

from __future__ import annotations

import re
import shutil
from typing import TYPE_CHECKING

import pygments
import pytest

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.testing.util import SphinxTestApp


def check_viewcode_output(app: SphinxTestApp) -> str:
    if tuple(map(int, pygments.__version__.split('.')[:2])) >= (2, 19):
        sp = '<span> </span>'
    else:
        sp = ' '

    warnings = re.sub(r'\\+', '/', app.warning.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include "
        r"file .*/spam/__init__.py'",
        warnings,
    )

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
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

    result = (app.outdir / '_modules/spam/mod1.html').read_text(encoding='utf8')
    # filter pygments classes
    result = re.sub('<span class="[^"]{,2}">', '<span>', result)
    assert (
        '<div class="viewcode-block" id="Class1">\n'
        '<a class="viewcode-back" href="../../index.html#spam.Class1">[docs]</a>\n'
    ) in result
    assert '<span>@decorator</span>\n' in result
    assert f'<span>class</span>{sp}<span>Class1</span><span>:</span>\n' in result
    assert (
        '<span>    </span>'
        '<span>&quot;&quot;&quot;this is Class1&quot;&quot;&quot;</span></div>\n'
    ) in result

    return result


@pytest.mark.sphinx(
    'html',
    testroot='ext-viewcode',
    freshenv=True,
    confoverrides={'viewcode_line_numbers': True},
)
@pytest.mark.usefixtures('rollback_sysmodules')
def test_viewcode_linenos(app: SphinxTestApp) -> None:
    shutil.rmtree(app.outdir / '_modules', ignore_errors=True)
    app.build(force_all=True)

    result = check_viewcode_output(app)
    assert '<span class="linenos"> 1</span>' in result


@pytest.mark.sphinx(
    'html',
    testroot='ext-viewcode',
    freshenv=True,
    confoverrides={'viewcode_line_numbers': False},
)
@pytest.mark.usefixtures('rollback_sysmodules')
def test_viewcode(app: SphinxTestApp) -> None:
    shutil.rmtree(app.outdir / '_modules', ignore_errors=True)
    app.build(force_all=True)

    result = check_viewcode_output(app)
    assert 'class="linenos">' not in result


@pytest.mark.sphinx('epub', testroot='ext-viewcode')
@pytest.mark.usefixtures('rollback_sysmodules')
def test_viewcode_epub_default(app: SphinxTestApp) -> None:
    shutil.rmtree(app.outdir)
    app.build(force_all=True)

    assert not (app.outdir / '_modules/spam/mod1.xhtml').exists()

    result = (app.outdir / 'index.xhtml').read_text(encoding='utf8')
    assert result.count('href="_modules/spam/mod1.xhtml#func1"') == 0


@pytest.mark.sphinx(
    'epub',
    testroot='ext-viewcode',
    confoverrides={'viewcode_enable_epub': True},
)
@pytest.mark.usefixtures('rollback_sysmodules')
def test_viewcode_epub_enabled(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    assert (app.outdir / '_modules/spam/mod1.xhtml').exists()

    result = (app.outdir / 'index.xhtml').read_text(encoding='utf8')
    assert result.count('href="_modules/spam/mod1.xhtml#func1"') == 2


@pytest.mark.sphinx('html', testroot='ext-viewcode', tags=['test_linkcode'])
def test_linkcode(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'objects.rst'])

    stuff = (app.outdir / 'objects.html').read_text(encoding='utf8')

    assert 'https://foobar/source/foolib.py' in stuff
    assert 'https://foobar/js/' in stuff
    assert 'https://foobar/c/' in stuff
    assert 'https://foobar/cpp/' in stuff
    assert 'http://foobar/rst/' in stuff


@pytest.mark.sphinx('html', testroot='ext-viewcode-find', freshenv=True)
def test_local_source_files(app: SphinxTestApp) -> None:
    def find_source(
        app: Sphinx, modname: str
    ) -> tuple[str, dict[str, tuple[str, int, int]]]:
        if modname == 'not_a_package':
            source = app.srcdir / 'not_a_package/__init__.py'
            tags = {
                'func1': ('def', 1, 1),
                'Class1': ('class', 1, 1),
                'not_a_package.submodule.func1': ('def', 1, 1),
                'not_a_package.submodule.Class1': ('class', 1, 1),
            }
        else:
            source = app.srcdir / 'not_a_package/submodule.py'
            tags = {
                'not_a_package.submodule.func1': ('def', 11, 15),
                'Class1': ('class', 19, 22),
                'not_a_package.submodule.Class1': ('class', 19, 22),
                'Class3': ('class', 25, 30),
                'not_a_package.submodule.Class3.class_attr': ('other', 29, 29),
            }
        return source.read_text(encoding='utf8'), tags

    app.connect('viewcode-find-source', find_source)
    app.build(force_all=True)

    warnings = re.sub(r'\\+', '/', app.warning.getvalue())
    assert re.findall(
        r"index.rst:\d+: WARNING: Object named 'func1' not found in include "
        r"file .*/not_a_package/__init__.py'",
        warnings,
    )

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    for needle in (
        'href="_modules/not_a_package.html#func1"',
        'href="_modules/not_a_package.html#not_a_package.submodule.func1"',
        'href="_modules/not_a_package/submodule.html#Class1"',
        'href="_modules/not_a_package/submodule.html#Class3"',
        'href="_modules/not_a_package/submodule.html#not_a_package.submodule.Class1"',
        'href="_modules/not_a_package/submodule.html#not_a_package.submodule.Class3.class_attr"',
        'This is the class attribute class_attr',
    ):
        assert result.count(needle) == 1


@pytest.mark.sphinx('html', testroot='ext-viewcode-find-package', freshenv=True)
def test_find_local_package_import_path(app: Sphinx) -> None:
    app.build(force_all=True)
    result = (app.outdir / 'index.html').read_text(encoding='utf8')

    count_func1 = result.count(
        'href="_modules/main_package/subpackage/_subpackage2/submodule.html#func1"'
    )
    assert count_func1 == 1

    count_class1 = result.count(
        'href="_modules/main_package/subpackage/_subpackage2/submodule.html#Class1"'
    )
    assert count_class1 == 1

    count_class3 = result.count(
        'href="_modules/main_package/subpackage/_subpackage2/submodule.html#Class3"'
    )
    assert count_class3 == 1
