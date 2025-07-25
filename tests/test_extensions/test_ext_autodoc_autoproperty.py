"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.test_extensions.autodoc_util import do_autodoc

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_properties(app: SphinxTestApp) -> None:
    actual = do_autodoc(app, 'property', 'target.properties.Foo.prop1')
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop1',
        '   :module: target.properties',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_properties(app: SphinxTestApp) -> None:
    actual = do_autodoc(app, 'property', 'target.properties.Foo.prop2')
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop2',
        '   :module: target.properties',
        '   :classmethod:',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_properties_with_type_comment(app: SphinxTestApp) -> None:
    actual = do_autodoc(
        app, 'property', 'target.properties.Foo.prop1_with_type_comment'
    )
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop1_with_type_comment',
        '   :module: target.properties',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_properties_with_type_comment(app: SphinxTestApp) -> None:
    actual = do_autodoc(
        app, 'property', 'target.properties.Foo.prop2_with_type_comment'
    )
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop2_with_type_comment',
        '   :module: target.properties',
        '   :classmethod:',
        '   :type: int',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_cached_properties(app: SphinxTestApp) -> None:
    actual = do_autodoc(app, 'property', 'target.cached_property.Foo.prop')
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop',
        '   :module: target.cached_property',
        '   :type: int',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_cached_properties_with_type_comment(app: SphinxTestApp) -> None:
    actual = do_autodoc(
        app, 'property', 'target.cached_property.Foo.prop_with_type_comment'
    )
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop_with_type_comment',
        '   :module: target.cached_property',
        '   :type: int',
        '',
    ]
