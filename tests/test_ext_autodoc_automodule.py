"""
    test_ext_autodoc_autocmodule
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from .test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_empty_all(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.empty_all', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.empty_all',
        '',
        'docsting of empty_all module.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_automodule(app):
    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.module', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.module',
        '',
        '',
        '.. py:data:: annotated',
        '   :module: target.module',
        '   :type: int',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: documented',
        '   :module: target.module',
        '   :value: 1',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_automodule_undoc_members(app):
    options = {'members': None,
               'undoc-members': None}
    actual = do_autodoc(app, 'module', 'target.module', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.module',
        '',
        '',
        '.. py:data:: annotated',
        '   :module: target.module',
        '   :type: int',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: documented',
        '   :module: target.module',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: undoc_annotated',
        '   :module: target.module',
        '   :type: int',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_automodule_special_members(app):
    options = {'members': None,
               'special-members': None}
    actual = do_autodoc(app, 'module', 'target.module', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.module',
        '',
        '',
        '.. py:data:: __documented_special__',
        '   :module: target.module',
        '   :value: 1',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: annotated',
        '   :module: target.module',
        '   :type: int',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: documented',
        '   :module: target.module',
        '   :value: 1',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_mock_imports': ['missing_module',
                                                            'missing_package1',
                                                            'missing_package2',
                                                            'missing_package3',
                                                            'sphinx.missing_module4']})
@pytest.mark.usefixtures("rollback_sysmodules")
def test_subclass_of_mocked_object(app):
    sys.modules.pop('target', None)  # unload target module to clear the module cache

    options = {'members': None}
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert '.. py:class:: Inherited(*args: Any, **kwargs: Any)' in actual
