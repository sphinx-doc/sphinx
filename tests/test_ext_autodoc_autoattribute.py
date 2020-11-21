"""
    test_ext_autodoc_autoattribute
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from .test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute(app):
    actual = do_autodoc(app, 'attribute', 'target.Class.attr')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        "   :value: 'bar'",
        '',
        '   should be documented -- süß',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_novalue(app):
    options = {'no-value': True}
    actual = do_autodoc(app, 'attribute', 'target.Class.attr', options)
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        '',
        '   should be documented -- süß',
        '',
    ]


@pytest.mark.skipif(sys.version_info < (3, 6), reason='python 3.6+ is required.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_typed_variable(app):
    actual = do_autodoc(app, 'attribute', 'target.typed_vars.Class.attr2')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr2',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
    ]


@pytest.mark.skipif(sys.version_info < (3, 6), reason='python 3.6+ is required.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_instance_variable(app):
    actual = do_autodoc(app, 'attribute', 'target.typed_vars.Class.attr4')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.attr4',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
        '   attr4',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_NewType(app):
    actual = do_autodoc(app, 'attribute', 'target.typevar.Class.T6')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :class:`int`',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoattribute_TypeVar(app):
    actual = do_autodoc(app, 'attribute', 'target.typevar.Class.T1')
    assert list(actual) == [
        '',
        '.. py:attribute:: Class.T1',
        '   :module: target.typevar',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
    ]
