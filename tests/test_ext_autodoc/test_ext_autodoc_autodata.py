"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import pytest

from tests.test_ext_autodoc.autodoc_util import do_autodoc

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_autodata() -> None:
    actual = do_autodoc('data', 'target.integer')
    assert actual == [
        '',
        '.. py:data:: integer',
        '   :module: target',
        '   :value: 1',
        '',
        '   documentation for the integer',
        '',
    ]


def test_autodata_novalue() -> None:
    options = {'no-value': None}
    actual = do_autodoc('data', 'target.integer', options=options)
    assert actual == [
        '',
        '.. py:data:: integer',
        '   :module: target',
        '',
        '   documentation for the integer',
        '',
    ]


def test_autodata_typed_variable() -> None:
    actual = do_autodoc('data', 'target.typed_vars.attr2')
    assert actual == [
        '',
        '.. py:data:: attr2',
        '   :module: target.typed_vars',
        '   :type: str',
        '',
        '   attr2',
        '',
    ]


def test_autodata_type_comment() -> None:
    actual = do_autodoc('data', 'target.typed_vars.attr3')
    assert actual == [
        '',
        '.. py:data:: attr3',
        '   :module: target.typed_vars',
        '   :type: str',
        "   :value: ''",
        '',
        '   attr3',
        '',
    ]


def test_autodata_GenericAlias() -> None:
    actual = do_autodoc('data', 'target.genericalias.T')
    assert actual == [
        '',
        '.. py:data:: T',
        '   :module: target.genericalias',
        '',
        '   A list of int',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
    ]


def test_autodata_hide_value() -> None:
    actual = do_autodoc('data', 'target.hide_value.SENTINEL1')
    assert actual == [
        '',
        '.. py:data:: SENTINEL1',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '   :meta hide-value:',
        '',
    ]

    actual = do_autodoc('data', 'target.hide_value.SENTINEL2')
    assert actual == [
        '',
        '.. py:data:: SENTINEL2',
        '   :module: target.hide_value',
        '',
        '   :meta hide-value:',
        '',
    ]
