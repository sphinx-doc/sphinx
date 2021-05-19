"""
    test_ext_autodoc_autoclass
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from typing import List, Union

import pytest

from .test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_classes(app):
    actual = do_autodoc(app, 'function', 'target.classes.Foo')
    assert list(actual) == [
        '',
        '.. py:function:: Foo()',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc(app, 'function', 'target.classes.Bar')
    assert list(actual) == [
        '',
        '.. py:function:: Bar(x, y)',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc(app, 'function', 'target.classes.Baz')
    assert list(actual) == [
        '',
        '.. py:function:: Baz(x, y)',
        '   :module: target.classes',
        '',
    ]

    actual = do_autodoc(app, 'function', 'target.classes.Qux')
    assert list(actual) == [
        '',
        '.. py:function:: Qux(foo, bar)',
        '   :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_instance_variable(app):
    options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.instance_variable.Bar', options)
    assert list(actual) == [
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_inherited_instance_variable(app):
    options = {'members': None,
               'inherited-members': None}
    actual = do_autodoc(app, 'class', 'target.instance_variable.Bar', options)
    assert list(actual) == [
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


@pytest.mark.skipif(sys.version_info < (3, 6), reason='py36+ is available since python3.6.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_uninitialized_attributes(app):
    options = {"members": None,
               "inherited-members": None}
    actual = do_autodoc(app, 'class', 'target.uninitialized_attributes.Derived', options)
    assert list(actual) == [
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


@pytest.mark.skipif(sys.version_info < (3, 6), reason='py36+ is available since python3.6.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_undocumented_uninitialized_attributes(app):
    options = {"members": None,
               "inherited-members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'class', 'target.uninitialized_attributes.Derived', options)
    assert list(actual) == [
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


def test_decorators(app):
    actual = do_autodoc(app, 'class', 'target.decorator.Baz')
    assert list(actual) == [
        '',
        '.. py:class:: Baz(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]

    actual = do_autodoc(app, 'class', 'target.decorator.Qux')
    assert list(actual) == [
        '',
        '.. py:class:: Qux(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]

    actual = do_autodoc(app, 'class', 'target.decorator.Quux')
    assert list(actual) == [
        '',
        '.. py:class:: Quux(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_properties(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.properties.Foo', options)
    assert list(actual) == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.properties',
        '',
        '   docstring',
        '',
        '',
        '   .. py:property:: Foo.prop',
        '      :module: target.properties',
        '      :type: int',
        '',
        '      docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_slots_attribute(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.slots.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar()',
        '   :module: target.slots',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Bar.attr1',
        '      :module: target.slots',
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


@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required.')
@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_show_inheritance_for_subclass_of_generic_type(app):
    options = {'show-inheritance': None}
    actual = do_autodoc(app, 'class', 'target.classes.Quux', options)
    assert list(actual) == [
        '',
        '.. py:class:: Quux(iterable=(), /)',
        '   :module: target.classes',
        '',
        '   Bases: :class:`~typing.List`\\ '
        '[:obj:`~typing.Union`\\ [:class:`int`, :class:`float`]]',
        '',
        '   A subclass of List[Union[int, float]]',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_process_bases(app):
    def autodoc_process_bases(app, name, obj, options, bases):
        assert name == 'target.classes.Quux'
        assert obj.__module__ == 'target.classes'
        assert obj.__name__ == 'Quux'
        assert options == {'show-inheritance': True,
                           'members': []}
        assert bases == [List[Union[int, float]]]

        bases.pop()
        bases.extend([int, str])

    app.connect('autodoc-process-bases', autodoc_process_bases)

    options = {'show-inheritance': None}
    actual = do_autodoc(app, 'class', 'target.classes.Quux', options)
    if sys.version_info < (3, 7):
        assert list(actual) == [
            '',
            '.. py:class:: Quux(*args, **kwds)',
            '   :module: target.classes',
            '',
            '   Bases: :class:`int`, :class:`str`',
            '',
            '   A subclass of List[Union[int, float]]',
            '',
        ]
    else:
        assert list(actual) == [
            '',
            '.. py:class:: Quux(iterable=(), /)',
            '   :module: target.classes',
            '',
            '   Bases: :class:`int`, :class:`str`',
            '',
            '   A subclass of List[Union[int, float]]',
            '',
        ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_doc_from_class(app):
    options = {"members": None,
               "class-doc-from": "class"}
    actual = do_autodoc(app, 'class', 'target.autoclass_content.C', options)
    assert list(actual) == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_doc_from_init(app):
    options = {"members": None,
               "class-doc-from": "init"}
    actual = do_autodoc(app, 'class', 'target.autoclass_content.C', options)
    assert list(actual) == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_class_doc_from_both(app):
    options = {"members": None,
               "class-doc-from": "both"}
    actual = do_autodoc(app, 'class', 'target.autoclass_content.C', options)
    assert list(actual) == [
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '   __init__ docstring',
        '',
    ]


def test_class_alias(app):
    def autodoc_process_docstring(*args):
        """A handler always raises an error.
        This confirms this handler is never called for class aliases.
        """
        raise

    app.connect('autodoc-process-docstring', autodoc_process_docstring)
    actual = do_autodoc(app, 'class', 'target.classes.Alias')
    assert list(actual) == [
        '',
        '.. py:attribute:: Alias',
        '   :module: target.classes',
        '',
        '   alias of :class:`target.classes.Foo`',
    ]


def test_class_alias_having_doccomment(app):
    actual = do_autodoc(app, 'class', 'target.classes.OtherAlias')
    assert list(actual) == [
        '',
        '.. py:attribute:: OtherAlias',
        '   :module: target.classes',
        '',
        '   docstring',
        '',
    ]
