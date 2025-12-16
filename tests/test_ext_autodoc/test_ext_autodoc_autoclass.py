"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import sys
import typing

import pytest

from tests.test_ext_autodoc.autodoc_util import FakeEvents, do_autodoc

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')


def test_classes() -> None:
    actual = do_autodoc('function', 'target.classes.Foo')
    assert actual == [
        '',
        '.. py:function:: Foo()',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc('function', 'target.classes.Bar')
    assert actual == [
        '',
        '.. py:function:: Bar(x, y)',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc('function', 'target.classes.Baz')
    assert actual == [
        '',
        '.. py:function:: Baz(x, y)',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc('function', 'target.classes.Qux')
    assert actual == [
        '',
        '.. py:function:: Qux(foo, bar)',
        '   :module: target.classes',
        '',
    ]


def test_instance_variable() -> None:
    options = {'members': None}
    actual = do_autodoc('class', 'target.instance_variable.Bar', options=options)
    assert actual == [
        '',
        '.. py:class:: Bar()',
        '   :module: target.instance_variable',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
        '',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
    ]


def test_inherited_instance_variable() -> None:
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc('class', 'target.instance_variable.Bar', options=options)
    assert actual == [
        '',
        '.. py:class:: Bar()',
        '   :module: target.instance_variable',
        '',
        '',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.instance_variable',
        '',
        '      docstring foo',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
        '',
        '   .. py:attribute:: Bar.attr3',
        '      :module: target.instance_variable',
        '',
        '      docstring bar',
        '',
    ]


def test_uninitialized_attributes() -> None:
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(
        'class', 'target.uninitialized_attributes.Derived', options=options
    )
    assert actual == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.uninitialized_attributes',
        '',
        '',
        '   .. py:attribute:: Derived.attr1',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Derived.attr3',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
    ]


def test_undocumented_uninitialized_attributes() -> None:
    options = {
        'members': None,
        'inherited-members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(
        'class', 'target.uninitialized_attributes.Derived', options=options
    )
    assert actual == [
        '',
        '.. py:class:: Derived()',
        '   :module: target.uninitialized_attributes',
        '',
        '',
        '   .. py:attribute:: Derived.attr1',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Derived.attr2',
        '      :module: target.uninitialized_attributes',
        '      :type: str',
        '',
        '',
        '   .. py:attribute:: Derived.attr3',
        '      :module: target.uninitialized_attributes',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Derived.attr4',
        '      :module: target.uninitialized_attributes',
        '      :type: str',
        '',
    ]


def test_decorators() -> None:
    actual = do_autodoc('class', 'target.decorator.Baz')
    assert actual == [
        '',
        '.. py:class:: Baz(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]

    actual = do_autodoc('class', 'target.decorator.Qux')
    assert actual == [
        '',
        '.. py:class:: Qux(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]

    actual = do_autodoc('class', 'target.decorator.Quux')
    assert actual == [
        '',
        '.. py:class:: Quux(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


def test_properties() -> None:
    if sys.version_info[:2] >= (3, 14):
        type_checking_only_name = 'TypeCheckingOnlyName'
    else:
        type_checking_only_name = 'int'

    options = {'members': None}
    actual = do_autodoc('class', 'target.properties.Foo', options=options)
    assert actual == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.properties',
        '',
        '   docstring',
        '',
        '',
        '   .. py:property:: Foo.prop1',
        '      :module: target.properties',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop1_with_type_comment',
        '      :module: target.properties',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop2',
        '      :module: target.properties',
        '      :classmethod:',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop2_with_type_comment',
        '      :module: target.properties',
        '      :classmethod:',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:property:: Foo.prop3_with_undefined_anotation',
        '      :module: target.properties',
        f'      :type: {type_checking_only_name}',
        '',
        '      docstring',
        '',
    ]


def test_slots_attribute() -> None:
    options = {'members': None}
    actual = do_autodoc('class', 'target.slots.Bar', options=options)
    assert actual == [
        '',
        '.. py:class:: Bar()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.slots',
        '      :type: int',
        '',
        '      docstring of attr1',
        '',
        '',
        '   .. py:attribute:: Bar.attr2',
        '      :module: target.slots',
        '',
        '      docstring of instance attr2',
        '',
    ]


def test_show_inheritance_for_subclass_of_generic_type() -> None:
    options = {'show-inheritance': None}
    actual = do_autodoc('class', 'target.classes.Quux', options=options)
    assert actual == [
        '',
        '.. py:class:: Quux(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :py:class:`~typing.List`\\ [:py:class:`int` | :py:class:`float`]',
        '',
        '   A subclass of List[Union[int, float]]',
        '',
    ]


def test_show_inheritance_for_decendants_of_generic_type() -> None:
    options = {'show-inheritance': None}
    actual = do_autodoc('class', 'target.classes.Corge', options=options)
    assert actual == [
        '',
        '.. py:class:: Corge(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :py:class:`~target.classes.Quux`',
        '',
    ]


def _autodoc_process_bases(
    app: Sphinx, name: str, obj: Any, options: Any, bases: list[type]
) -> None:
    assert name == 'target.classes.Quux'
    assert obj.__module__ == 'target.classes'
    assert obj.__name__ == 'Quux'
    assert vars(options) == {}
    assert bases == [typing.List[typing.Union[int, float]]]  # NoQA: UP006, UP007

    bases.pop()
    bases.extend([int, str])


def test_autodoc_process_bases() -> None:
    events = FakeEvents()
    events.connect('autodoc-process-bases', _autodoc_process_bases)

    options = {'show-inheritance': None}
    actual = do_autodoc('class', 'target.classes.Quux', events=events, options=options)
    assert actual == [
        '',
        '.. py:class:: Quux(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :py:class:`int`, :py:class:`str`',
        '',
        '   A subclass of List[Union[int, float]]',
        '',
    ]


def test_class_doc_from_class() -> None:
    options = {
        'members': None,
        'class-doc-from': 'class',
    }
    actual = do_autodoc('class', 'target.autoclass_content.C', options=options)
    assert actual == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
    ]


def test_class_doc_from_init() -> None:
    options = {
        'members': None,
        'class-doc-from': 'init',
    }
    actual = do_autodoc('class', 'target.autoclass_content.C', options=options)
    assert actual == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
    ]


def test_class_doc_from_both() -> None:
    options = {
        'members': None,
        'class-doc-from': 'both',
    }
    actual = do_autodoc('class', 'target.autoclass_content.C', options=options)
    assert actual == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '   __init__ docstring',
        '',
    ]


def test_class_alias() -> None:
    def autodoc_process_docstring(*args: Any) -> None:
        """A handler always raises an error.
        This confirms this handler is never called for class aliases.
        """
        raise RuntimeError

    events = FakeEvents()
    events.connect('autodoc-process-docstring', autodoc_process_docstring)
    actual = do_autodoc('class', 'target.classes.Alias', events=events)
    assert actual == [
        '',
        '.. py:attribute:: Alias',
        '   :module: target.classes',
        '',
        '   alias of :py:class:`~target.classes.Foo`',
    ]


def test_class_alias_having_doccomment() -> None:
    actual = do_autodoc('class', 'target.classes.OtherAlias')
    assert actual == [
        '',
        '.. py:attribute:: OtherAlias',
        '   :module: target.classes',
        '',
        '   docstring',
        '',
    ]


def test_class_alias_for_imported_object_having_doccomment() -> None:
    actual = do_autodoc('class', 'target.classes.IntAlias')
    assert actual == [
        '',
        '.. py:attribute:: IntAlias',
        '   :module: target.classes',
        '',
        '   docstring',
        '',
    ]


def test_coroutine() -> None:
    options = {'members': None}
    actual = do_autodoc('class', 'target.coroutine.AsyncClass', options=options)
    assert actual == [
        '',
        '.. py:class:: AsyncClass()',
        '   :module: target.coroutine',
        '',
        '',
        '   .. py:method:: AsyncClass.do_asyncgen()',
        '      :module: target.coroutine',
        '      :async:',
        '',
        '      A documented async generator',
        '',
        '',
        '   .. py:method:: AsyncClass.do_coroutine()',
        '      :module: target.coroutine',
        '      :async:',
        '',
        '      A documented coroutine function',
        '',
        '',
        '   .. py:method:: AsyncClass.do_coroutine2()',
        '      :module: target.coroutine',
        '      :async:',
        '      :classmethod:',
        '',
        '      A documented coroutine classmethod',
        '',
        '',
        '   .. py:method:: AsyncClass.do_coroutine3()',
        '      :module: target.coroutine',
        '      :async:',
        '      :staticmethod:',
        '',
        '      A documented coroutine staticmethod',
        '',
    ]


def test_autodata_NewType_module_level() -> None:
    actual = do_autodoc('class', 'target.typevar.T6')
    assert actual == [
        '',
        '.. py:class:: T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`~datetime.date`',
        '',
    ]


def test_autoattribute_NewType_class_level() -> None:
    actual = do_autodoc('class', 'target.typevar.Class.T6')
    assert actual == [
        '',
        '.. py:class:: Class.T6',
        '   :module: target.typevar',
        '',
        '   T6',
        '',
        '   alias of :py:class:`~datetime.date`',
        '',
    ]


def test_autodata_TypeVar_class_level() -> None:
    actual = do_autodoc('class', 'target.typevar.T1')
    assert actual == [
        '',
        '.. py:class:: T1',
        '   :module: target.typevar',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
    ]


def test_autoattribute_TypeVar_module_level() -> None:
    actual = do_autodoc('class', 'target.typevar.Class.T1')
    assert actual == [
        '',
        '.. py:class:: Class.T1',
        '   :module: target.typevar',
        '',
        '   T1',
        '',
        "   alias of TypeVar('T1')",
        '',
    ]


def test_inherited_instance_variable_with_annotations() -> None:
    options = {
        'members': None,
        'inherited-members': None,
    }
    actual = do_autodoc(
        'class', 'target.inherited_annotations.NoTypeAnnotation', options=options
    )
    assert actual == [
        '',
        '.. py:class:: NoTypeAnnotation()',
        '   :module: target.inherited_annotations',
        '',
        '',
        '   .. py:attribute:: NoTypeAnnotation.a',
        '      :module: target.inherited_annotations',
        '      :value: 1',
        '',
        '      Local',
        '',
        '',
        '   .. py:attribute:: NoTypeAnnotation.inherit_me',
        '      :module: target.inherited_annotations',
        '      :type: int',
        '',
        '      Inherited',
        '',
    ]


def test_no_inherited_instance_variable_with_annotations() -> None:
    options = {'members': None}
    actual = do_autodoc(
        'class', 'target.inherited_annotations.NoTypeAnnotation2', options=options
    )
    assert actual == [
        '',
        '.. py:class:: NoTypeAnnotation2()',
        '   :module: target.inherited_annotations',
        '',
        '',
        '   .. py:attribute:: NoTypeAnnotation2.a',
        '      :module: target.inherited_annotations',
        '      :value: 1',
        '',
        '      Local',
        '',
    ]
