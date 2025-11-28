"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import inspect
import sys
import typing

import pytest

from sphinx.ext.autodoc._dynamic._mock import _MockObject
from sphinx.ext.autodoc._shared import _AutodocConfig

from tests.test_ext_autodoc.autodoc_util import do_autodoc

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_empty_all() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.empty_all', options=options)
    assert actual == [
        '',
        '.. py:module:: target.empty_all',
        '',
        '   docsting of empty_all module.',
        '',
    ]


def test_automodule() -> None:
    options = {'members': None}
    actual = do_autodoc('module', 'target.module', options=options)
    assert actual == [
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


def test_automodule_undoc_members() -> None:
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('module', 'target.module', options=options)
    assert actual == [
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


def test_automodule_special_members() -> None:
    options = {
        'members': None,
        'special-members': None,
    }
    actual = do_autodoc('module', 'target.module', options=options)
    assert actual == [
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


def test_automodule_inherited_members() -> None:
    options = {
        'members': None,
        'undoc-members': None,
        'inherited-members': 'Base, list',
    }
    actual = do_autodoc('module', 'target.inheritance', options=options)
    assert actual == [
        '',
        '.. py:module:: target.inheritance',
        '',
        '',
        '.. py:class:: AnotherBase()',
        '   :module: target.inheritance',
        '',
        '',
        '   .. py:method:: AnotherBase.another_inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Another inherited function.',
        '',
        '',
        '.. py:class:: Base()',
        '   :module: target.inheritance',
        '',
        '',
        '   .. py:attribute:: Base.inheritedattr',
        '      :module: target.inheritance',
        '      :value: None',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Base.inheritedclassmeth()',
        '      :module: target.inheritance',
        '      :classmethod:',
        '',
        '      Inherited class method.',
        '',
        '',
        '   .. py:method:: Base.inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Inherited function.',
        '',
        '',
        '   .. py:method:: Base.inheritedstaticmeth(cls)',
        '      :module: target.inheritance',
        '      :staticmethod:',
        '',
        '      Inherited static method.',
        '',
        '',
        '.. py:class:: Derived()',
        '   :module: target.inheritance',
        '',
        '',
        '   .. py:method:: Derived.another_inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Another inherited function.',
        '',
        '',
        '   .. py:method:: Derived.inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Inherited function.',
        '',
        '',
        '.. py:class:: MyList(iterable=(), /)',
        '   :module: target.inheritance',
        '',
        '',
        '   .. py:method:: MyList.meth()',
        '      :module: target.inheritance',
        '',
        '      docstring',
        '',
    ]


@pytest.mark.usefixtures('rollback_sysmodules')
def test_subclass_of_mocked_object() -> None:
    config = _AutodocConfig(
        autodoc_mock_imports=[
            'missing_module',
            'missing_package1',
            'missing_package2',
            'missing_package3',
            'sphinx.missing_module4',
        ]
    )

    sys.modules.pop('target', None)  # unload target module to clear the module cache

    options = {'members': None}
    actual = do_autodoc('module', 'target.need_mocks', config=config, options=options)
    # ``typing.Any`` is not available at runtime on ``_MockObject.__new__``
    assert actual[10:11] == [
        '.. py:class:: Inherited(*args: Any, **kwargs: Any)',
    ]

    # make ``typing.Any`` available at runtime on ``_MockObject.__new__``
    sig = inspect.signature(_MockObject.__new__)
    parameters = sig.parameters.copy()
    for name in ('args', 'kwargs'):
        parameters[name] = parameters[name].replace(annotation=typing.Any)
    sig = sig.replace(parameters=tuple(parameters.values()))
    _MockObject.__new__.__signature__ = sig  # type: ignore[attr-defined]

    options = {'members': None}
    actual = do_autodoc('module', 'target.need_mocks', config=config, options=options)
    assert actual[10:11] == [
        '.. py:class:: Inherited(*args: ~typing.Any, **kwargs: ~typing.Any)',
    ]
