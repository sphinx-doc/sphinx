"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

import pytest

from tests.test_extensions.autodoc_util import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata(app):
    actual = do_autodoc(app, 'data', 'target.integer')
    assert list(actual) == [
        '',
        '.. py:data:: integer',
        '   :module: target',
        '   :value: 1',
        '',
        '   documentation for the integer',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_novalue(app):
    options = {'no-value': None}
    actual = do_autodoc(app, 'data', 'target.integer', options)
    assert list(actual) == [
        '',
        '.. py:data:: integer',
        '   :module: target',
        '',
        '   documentation for the integer',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_typed_variable(app):
    actual = do_autodoc(app, 'data', 'target.typed_vars.attr2')
    assert list(actual) == [
        '',
        '.. py:data:: attr2',
        '   :module: target.typed_vars',
        '   :type: str',
        '',
        '   attr2',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_type_comment(app):
    actual = do_autodoc(app, 'data', 'target.typed_vars.attr3')
    assert list(actual) == [
        '',
        '.. py:data:: attr3',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr3',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_GenericAlias(app):
    actual = do_autodoc(app, 'data', 'target.genericalias.T')
    assert list(actual) == [
        '',
        '.. py:data:: T',
        '   :module: target.genericalias',
        '',
        '   A list of int',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodata_hide_value(app):
    actual = do_autodoc(app, 'data', 'target.hide_value.SENTINEL1')
    assert list(actual) == [
        '',
        '.. py:data:: SENTINEL1',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '   :meta hide-value:',
        '',
    ]

    actual = do_autodoc(app, 'data', 'target.hide_value.SENTINEL2')
    assert list(actual) == [
        '',
        '.. py:data:: SENTINEL2',
        '   :module: target.hide_value',
        '',
        '   :meta hide-value:',
        '',
    ]
