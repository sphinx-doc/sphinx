"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import pytest

from tests.test_ext_autodoc.autodoc_util import do_autodoc

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_autoattribute() -> None:
    actual = do_autodoc('attribute', 'target.Class.attr')
    assert actual == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        "   :value: 'bar'",
        '',
        '   should be documented -- süß',
        '',
    ]


def test_autoattribute_novalue() -> None:
    options = {'no-value': None}
    actual = do_autodoc('attribute', 'target.Class.attr', options=options)
    assert actual == [
        '',
        '.. py:attribute:: Class.attr',
        '   :module: target',
        '',
        '   should be documented -- süß',
        '',
    ]


def test_autoattribute_typed_variable() -> None:
    actual = do_autodoc('attribute', 'target.typed_vars.Class.attr2')
    assert actual == [
        '',
        '.. py:attribute:: Class.attr2',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
    ]


def test_autoattribute_typed_variable_in_alias() -> None:
    actual = do_autodoc('attribute', 'target.typed_vars.Alias.attr2')
    assert actual == [
        '',
        '.. py:attribute:: Alias.attr2',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
    ]


def test_autoattribute_instance_variable() -> None:
    actual = do_autodoc('attribute', 'target.typed_vars.Class.attr4')
    assert actual == [
        '',
        '.. py:attribute:: Class.attr4',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
        '   attr4',
        '',
    ]


def test_autoattribute_instance_variable_in_alias() -> None:
    actual = do_autodoc('attribute', 'target.typed_vars.Alias.attr4')
    assert actual == [
        '',
        '.. py:attribute:: Alias.attr4',
        '   :module: target.typed_vars',
        '   :type: int',
        '',
        '   attr4',
        '',
    ]


def test_autoattribute_instance_variable_without_comment() -> None:
    actual = do_autodoc('attribute', 'target.instance_variable.Bar.attr4')
    assert actual == [
        '',
        '.. py:attribute:: Bar.attr4',
        '   :module: target.instance_variable',
        '',
    ]


def test_autoattribute_slots_variable_list() -> None:
    actual = do_autodoc('attribute', 'target.slots.Foo.attr')
    assert actual == [
        '',
        '.. py:attribute:: Foo.attr',
        '   :module: target.slots',
        '',
    ]


def test_autoattribute_slots_variable_dict() -> None:
    actual = do_autodoc('attribute', 'target.slots.Bar.attr1')
    assert actual == [
        '',
        '.. py:attribute:: Bar.attr1',
        '   :module: target.slots',
        '   :type: int',
        '',
        '   docstring of attr1',
        '',
    ]


def test_autoattribute_slots_variable_str() -> None:
    actual = do_autodoc('attribute', 'target.slots.Baz.attr')
    assert actual == [
        '',
        '.. py:attribute:: Baz.attr',
        '   :module: target.slots',
        '',
    ]


def test_autoattribute_GenericAlias() -> None:
    actual = do_autodoc('attribute', 'target.genericalias.Class.T')
    assert actual == [
        '',
        '.. py:attribute:: Class.T',
        '   :module: target.genericalias',
        '',
        '   A list of int',
        '',
        '   alias of :py:class:`~typing.List`\\ [:py:class:`int`]',
        '',
    ]


def test_autoattribute_hide_value() -> None:
    actual = do_autodoc('attribute', 'target.hide_value.Foo.SENTINEL1')
    assert actual == [
        '',
        '.. py:attribute:: Foo.SENTINEL1',
        '   :module: target.hide_value',
        '',
        '   docstring',
        '',
        '   :meta hide-value:',
        '',
    ]

    actual = do_autodoc('attribute', 'target.hide_value.Foo.SENTINEL2')
    assert actual == [
        '',
        '.. py:attribute:: Foo.SENTINEL2',
        '   :module: target.hide_value',
        '',
        '   :meta hide-value:',
        '',
    ]
