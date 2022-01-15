"""
    test_ext_autodoc_autoproperty
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from .test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_properties(app):
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
def test_class_properties(app):
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


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_cached_properties(app):
    actual = do_autodoc(app, 'property', 'target.cached_property.Foo.prop')
    assert list(actual) == [
        '',
        '.. py:property:: Foo.prop',
        '   :module: target.cached_property',
        '   :type: int',
        '',
    ]
