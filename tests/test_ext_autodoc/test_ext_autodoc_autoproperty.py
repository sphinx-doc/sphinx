"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import sys

import pytest

from tests.test_ext_autodoc.autodoc_util import do_autodoc

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_properties() -> None:
    actual = do_autodoc('property', 'target.properties.Foo.prop1')
    assert actual == [
        '',
        '.. py:property:: Foo.prop1',
        '   :module: target.properties',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


def test_class_properties() -> None:
    actual = do_autodoc('property', 'target.properties.Foo.prop2')
    assert actual == [
        '',
        '.. py:property:: Foo.prop2',
        '   :module: target.properties',
        '   :classmethod:',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


def test_properties_with_type_comment() -> None:
    actual = do_autodoc('property', 'target.properties.Foo.prop1_with_type_comment')
    assert actual == [
        '',
        '.. py:property:: Foo.prop1_with_type_comment',
        '   :module: target.properties',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


def test_class_properties_with_type_comment() -> None:
    actual = do_autodoc('property', 'target.properties.Foo.prop2_with_type_comment')
    assert actual == [
        '',
        '.. py:property:: Foo.prop2_with_type_comment',
        '   :module: target.properties',
        '   :classmethod:',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


def test_cached_properties() -> None:
    actual = do_autodoc('property', 'target.cached_property.Foo.prop')
    assert actual == [
        '',
        '.. py:property:: Foo.prop',
        '   :module: target.cached_property',
        '   :type: int',
        '',
    ]


def test_cached_properties_with_type_comment() -> None:
    actual = do_autodoc('property', 'target.cached_property.Foo.prop_with_type_comment')
    assert actual == [
        '',
        '.. py:property:: Foo.prop_with_type_comment',
        '   :module: target.cached_property',
        '   :type: int',
        '',
    ]


def test_property_with_undefined_annotation() -> None:
    if sys.version_info[:2] >= (3, 14):
        type_checking_only_name = 'TypeCheckingOnlyName'
    else:
        type_checking_only_name = 'int'

    actual = do_autodoc(
        'property', 'target.properties.Foo.prop3_with_undefined_anotation'
    )
    assert actual == [
        '',
        '.. py:property:: Foo.prop3_with_undefined_anotation',
        '   :module: target.properties',
        f'   :type: {type_checking_only_name}',
        '',
        '   docstring',
        '',
    ]
