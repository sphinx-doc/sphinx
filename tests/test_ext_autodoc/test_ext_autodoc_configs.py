"""Test the autodoc extension.  This tests mainly for config variables"""

from __future__ import annotations

import logging
import platform
import sys

import pytest

from sphinx.ext.autodoc._shared import _AutodocConfig

from tests.test_ext_autodoc.autodoc_util import do_autodoc

pytestmark = pytest.mark.usefixtures('inject_autodoc_root_into_sys_path')

IS_PYPY = platform.python_implementation() == 'PyPy'


def test_autoclass_content_class() -> None:
    config = _AutodocConfig(autoclass_content='class')
    options = {'members': None}
    actual = do_autodoc(
        'module', 'target.autoclass_content', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.autoclass_content',
        '',
        '',
        '.. py:class:: A()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, no __new__',
        '',
        '',
        '.. py:class:: B()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__(no docstring), no __new__',
        '',
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__(no docstring)',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.autoclass_content',
        '',
        '   A class having both __init__ and __new__',
        '',
        '',
        '.. py:class:: G()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __init__ without docstring.',
        '',
        '',
        '.. py:class:: H()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __new__ without docstring.',
        '',
    ]


def test_autoclass_content_init() -> None:
    config = _AutodocConfig(autoclass_content='init')
    options = {'members': None}
    actual = do_autodoc(
        'module', 'target.autoclass_content', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.autoclass_content',
        '',
        '',
        '.. py:class:: A()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, no __new__',
        '',
        '',
        '.. py:class:: B()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__(no docstring), no __new__',
        '',
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__(no docstring)',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.autoclass_content',
        '',
        '   __new__ docstring',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: G()',
        '   :module: target.autoclass_content',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: H()',
        '   :module: target.autoclass_content',
        '',
        '   __new__ docstring',
        '',
    ]


def test_autodoc_class_signature_mixed() -> None:
    config = _AutodocConfig(autodoc_class_signature='mixed')
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.classes.Bar', config=config, options=options)
    assert actual == [
        '',
        '.. py:class:: Bar(x, y)',
        '   :module: target.classes',
        '',
    ]


def test_autodoc_class_signature_separated_init() -> None:
    config = _AutodocConfig(autodoc_class_signature='separated')
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.classes.Bar', config=config, options=options)
    assert actual == [
        '',
        '.. py:class:: Bar',
        '   :module: target.classes',
        '',
        '',
        '   .. py:method:: Bar.__init__(x, y)',
        '      :module: target.classes',
        '',
    ]


def test_autodoc_class_signature_separated_new() -> None:
    config = _AutodocConfig(autodoc_class_signature='separated')
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc('class', 'target.classes.Baz', config=config, options=options)
    assert actual == [
        '',
        '.. py:class:: Baz',
        '   :module: target.classes',
        '',
        '',
        '   .. py:method:: Baz.__new__(cls, x, y)',
        '      :module: target.classes',
        '      :staticmethod:',
        '',
    ]


def test_autoclass_content_both() -> None:
    config = _AutodocConfig(autoclass_content='both')
    options = {'members': None}
    actual = do_autodoc(
        'module', 'target.autoclass_content', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.autoclass_content',
        '',
        '',
        '.. py:class:: A()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, no __new__',
        '',
        '',
        '.. py:class:: B()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__(no docstring), no __new__',
        '',
        '',
        '.. py:class:: C()',
        '   :module: target.autoclass_content',
        '',
        '   A class having __init__, no __new__',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__(no docstring)',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.autoclass_content',
        '',
        '   A class having no __init__, __new__',
        '',
        '   __new__ docstring',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.autoclass_content',
        '',
        '   A class having both __init__ and __new__',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: G()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __init__ without docstring.',
        '',
        '   __init__ docstring',
        '',
        '',
        '.. py:class:: H()',
        '   :module: target.autoclass_content',
        '',
        '   A class inherits __new__ without docstring.',
        '',
        '   __new__ docstring',
        '',
    ]


def test_autodoc_inherit_docstrings() -> None:
    config = _AutodocConfig()
    assert config.autodoc_inherit_docstrings is True  # default
    actual = do_autodoc(
        'method', 'target.inheritance.Derived.inheritedmeth', config=config
    )
    assert actual == [
        '',
        '.. py:method:: Derived.inheritedmeth()',
        '   :module: target.inheritance',
        '',
        '   Inherited function.',
        '',
    ]

    # disable autodoc_inherit_docstrings
    config = _AutodocConfig(autodoc_inherit_docstrings=False)
    actual = do_autodoc(
        'method', 'target.inheritance.Derived.inheritedmeth', config=config
    )
    assert actual == [
        '',
        '.. py:method:: Derived.inheritedmeth()',
        '   :module: target.inheritance',
        '',
    ]


def test_autodoc_inherit_docstrings_for_inherited_members() -> None:
    config = _AutodocConfig()
    options = {
        'members': None,
        'inherited-members': None,
    }

    assert config.autodoc_inherit_docstrings is True  # default
    actual = do_autodoc(
        'class', 'target.inheritance.Derived', config=config, options=options
    )
    assert actual == [
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
        '   .. py:attribute:: Derived.inheritedattr',
        '      :module: target.inheritance',
        '      :value: None',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: Derived.inheritedclassmeth()',
        '      :module: target.inheritance',
        '      :classmethod:',
        '',
        '      Inherited class method.',
        '',
        '',
        '   .. py:method:: Derived.inheritedmeth()',
        '      :module: target.inheritance',
        '',
        '      Inherited function.',
        '',
        '',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
        '      :module: target.inheritance',
        '      :staticmethod:',
        '',
        '      Inherited static method.',
        '',
    ]

    # disable autodoc_inherit_docstrings
    config = _AutodocConfig(autodoc_inherit_docstrings=False)
    actual = do_autodoc(
        'class', 'target.inheritance.Derived', config=config, options=options
    )
    assert actual == [
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
        '   .. py:method:: Derived.inheritedclassmeth()',
        '      :module: target.inheritance',
        '      :classmethod:',
        '',
        '      Inherited class method.',
        '',
        '',
        '   .. py:method:: Derived.inheritedstaticmeth(cls)',
        '      :module: target.inheritance',
        '      :staticmethod:',
        '',
        '      Inherited static method.',
        '',
    ]


def test_autodoc_docstring_signature() -> None:
    options = {
        'members': None,
        'special-members': '__init__, __new__',
    }
    actual = do_autodoc('class', 'target.DocstringSig', options=options)
    assert actual == [
        '',
        # FIXME: Ideally this would instead be: `DocstringSig(d, e=1)` but
        # currently `ClassDocumenter` does not apply the docstring signature
        # logic when extracting a signature from a __new__ or __init__ method.
        '.. py:class:: DocstringSig(*new_args, **new_kwargs)',
        '   :module: target',
        '',
        '',
        '   .. py:method:: DocstringSig.__init__(self, a, b=1) -> None',
        '      :module: target',
        '',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.__new__(cls, d, e=1) -> DocstringSig',
        '      :module: target',
        '      :staticmethod:',
        '',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth(FOO, BAR=1) -> BAZ',
        '      :module: target',
        '',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth2()',
        '      :module: target',
        '',
        '      First line, no signature',
        '      Second line followed by indentation::',
        '',
        '          indented line',
        '',
        '',
        '   .. py:property:: DocstringSig.prop1',
        '      :module: target',
        '',
        '      First line of docstring',
        '',
        '',
        '   .. py:property:: DocstringSig.prop2',
        '      :module: target',
        '',
        '      First line of docstring',
        '      Second line of docstring',
        '',
    ]

    # disable autodoc_docstring_signature
    config = _AutodocConfig(autodoc_docstring_signature=False)
    actual = do_autodoc('class', 'target.DocstringSig', config=config, options=options)
    assert actual == [
        '',
        '.. py:class:: DocstringSig(*new_args, **new_kwargs)',
        '   :module: target',
        '',
        '',
        '   .. py:method:: DocstringSig.__init__(*init_args, **init_kwargs)',
        '      :module: target',
        '',
        '      __init__(self, a, b=1) -> None',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.__new__(cls, *new_args, **new_kwargs)',
        '      :module: target',
        '      :staticmethod:',
        '',
        '      __new__(cls, d, e=1) -> DocstringSig',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth()',
        '      :module: target',
        '',
        '      meth(FOO, BAR=1) -> BAZ',
        '      First line of docstring',
        '',
        '      rest of docstring',
        '',
        '',
        '   .. py:method:: DocstringSig.meth2()',
        '      :module: target',
        '',
        '      First line, no signature',
        '      Second line followed by indentation::',
        '',
        '          indented line',
        '',
        '',
        '   .. py:property:: DocstringSig.prop1',
        '      :module: target',
        '',
        '      DocstringSig.prop1(self)',
        '      First line of docstring',
        '',
        '',
        '   .. py:property:: DocstringSig.prop2',
        '      :module: target',
        '',
        '      First line of docstring',
        '      Second line of docstring',
        '',
    ]


def test_autoclass_content_and_docstring_signature_class() -> None:
    config = _AutodocConfig(autoclass_content='class')
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(
        'module', 'target.docstring_signature', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.docstring_signature',
        '',
        '',
        '.. py:class:: A(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: B(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: C(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: D()',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: E()',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F()',
        '   :module: target.docstring_signature',
        '',
    ]


def test_autoclass_content_and_docstring_signature_init() -> None:
    config = _AutodocConfig(autoclass_content='init')
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(
        'module', 'target.docstring_signature', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.docstring_signature',
        '',
        '',
        '.. py:class:: A(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: B(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: C(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: D(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: E(foo: int, bar: int, baz: int)',
        '              E(foo: str, bar: str, baz: str)',
        '              E(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F(foo: int, bar: int, baz: int)',
        '              F(foo: str, bar: str, baz: str)',
        '              F(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
    ]


def test_autoclass_content_and_docstring_signature_both() -> None:
    config = _AutodocConfig(autoclass_content='both')
    options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(
        'module', 'target.docstring_signature', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.docstring_signature',
        '',
        '',
        '.. py:class:: A(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: B(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '   B(foo, bar, baz)',
        '',
        '',
        '.. py:class:: C(foo, bar)',
        '   :module: target.docstring_signature',
        '',
        '   C(foo, bar, baz)',
        '',
        '',
        '.. py:class:: D(foo, bar, baz)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: E(foo: int, bar: int, baz: int)',
        '              E(foo: str, bar: str, baz: str)',
        '              E(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F(foo: int, bar: int, baz: int)',
        '              F(foo: str, bar: str, baz: str)',
        '              F(foo: float, bar: float, baz: float)',
        '   :module: target.docstring_signature',
        '',
    ]


@pytest.mark.usefixtures('rollback_sysmodules')
def test_mocked_module_imports(caplog: pytest.LogCaptureFixture) -> None:
    # work around sphinx.util.logging.setup()
    logger = logging.getLogger('sphinx')
    logger.handlers[:] = [caplog.handler]
    caplog.set_level(logging.WARNING)

    sys.modules.pop('target', None)  # unload target module to clear the module cache

    # no autodoc_mock_imports
    options = {'members': 'TestAutodoc,decorated_function,func,Alias'}
    actual = do_autodoc(
        'module', 'target.need_mocks', expect_import_error=True, options=options
    )
    assert actual == []
    assert len(set(caplog.messages)) == 1
    assert "autodoc: failed to import 'need_mocks'" in caplog.messages[0]

    # with autodoc_mock_imports
    config = _AutodocConfig(
        autodoc_mock_imports=[
            'missing_module',
            'missing_package1',
            'missing_package2',
            'missing_package3',
            'sphinx.missing_module4',
        ]
    )

    caplog.clear()
    actual = do_autodoc('module', 'target.need_mocks', config=config, options=options)
    assert actual == [
        '',
        '.. py:module:: target.need_mocks',
        '',
        '',
        '.. py:data:: Alias',
        '   :module: target.need_mocks',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: TestAutodoc()',
        '   :module: target.need_mocks',
        '',
        '   TestAutodoc docstring.',
        '',
        '',
        '   .. py:attribute:: TestAutodoc.Alias',
        '      :module: target.need_mocks',
        '',
        '      docstring',
        '',
        '',
        '   .. py:method:: TestAutodoc.decorated_method()',
        '      :module: target.need_mocks',
        '',
        '      TestAutodoc::decorated_method docstring',
        '',
        '',
        '.. py:function:: decorated_function()',
        '   :module: target.need_mocks',
        '',
        '   decorated_function docstring',
        '',
        '',
        '.. py:function:: func(arg: missing_module.Class)',
        '   :module: target.need_mocks',
        '',
        '   a function takes mocked object as an argument',
        '',
    ]
    assert len(caplog.records) == 0


def test_autodoc_type_aliases() -> None:
    # default
    options = {'members': None}
    actual = do_autodoc('module', 'target.autodoc_type_aliases', options=options)
    assert actual == [
        '',
        '.. py:module:: target.autodoc_type_aliases',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr1',
        '      :module: target.autodoc_type_aliases',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr2',
        '      :module: target.autodoc_type_aliases',
        '      :type: int',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: mult(x: int, y: int) -> int',
        '                 mult(x: float, y: float) -> float',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: read(r: ~io.BytesIO) -> ~io.StringIO',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: sum(x: int, y: int) -> int',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable',
        '   :module: target.autodoc_type_aliases',
        '   :type: int',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable2',
        '   :module: target.autodoc_type_aliases',
        '   :type: int',
        '   :value: None',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable3',
        '   :module: target.autodoc_type_aliases',
        '   :type: int | None',
        '',
        '   docstring',
        '',
    ]

    # define aliases
    config = _AutodocConfig(
        autodoc_type_aliases={
            'myint': 'myint',
            'io.StringIO': 'my.module.StringIO',
        }
    )
    actual = do_autodoc(
        'module', 'target.autodoc_type_aliases', config=config, options=options
    )
    assert actual == [
        '',
        '.. py:module:: target.autodoc_type_aliases',
        '',
        '',
        '.. py:class:: Foo()',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr1',
        '      :module: target.autodoc_type_aliases',
        '      :type: myint',
        '',
        '      docstring',
        '',
        '',
        '   .. py:attribute:: Foo.attr2',
        '      :module: target.autodoc_type_aliases',
        '      :type: myint',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: mult(x: myint, y: myint) -> myint',
        '                 mult(x: float, y: float) -> float',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: read(r: ~io.BytesIO) -> my.module.StringIO',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:function:: sum(x: myint, y: myint) -> myint',
        '   :module: target.autodoc_type_aliases',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable',
        '   :module: target.autodoc_type_aliases',
        '   :type: myint',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable2',
        '   :module: target.autodoc_type_aliases',
        '   :type: myint',
        '   :value: None',
        '',
        '   docstring',
        '',
        '',
        '.. py:data:: variable3',
        '   :module: target.autodoc_type_aliases',
        '   :type: myint | None',
        '',
        '   docstring',
        '',
    ]


def test_autodoc_default_options() -> None:
    if sys.version_info[:3] >= (3, 12, 1):
        list_of_weak_references = '      list of weak references to the object'
    else:
        list_of_weak_references = '      list of weak references to the object (if defined)'  # fmt: skip

    # no settings
    actual = do_autodoc('class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    actual = do_autodoc('class', 'target.CustomIter')
    assert '   .. py:method:: target.CustomIter' not in actual
    actual = do_autodoc('module', 'target')
    assert '.. py:function:: function_to_be_imported(app)' not in actual

    # with :members:
    config = _AutodocConfig(autodoc_default_options={'members': True})
    actual = do_autodoc('class', 'target.enums.EnumCls', config=config)
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: = True
    config = _AutodocConfig(autodoc_default_options={'members': True})
    actual = do_autodoc('class', 'target.enums.EnumCls', config=config)
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: and :undoc-members:
    config = _AutodocConfig(
        autodoc_default_options={'members': True, 'undoc-members': True}
    )
    actual = do_autodoc('class', 'target.enums.EnumCls', config=config)
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' in actual

    # with :special-members:
    # Note that :members: must be *on* for :special-members: to work.
    config = _AutodocConfig(
        autodoc_default_options={'members': True, 'special-members': True}
    )
    actual = do_autodoc('class', 'target.CustomIter', config=config)
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert list_of_weak_references in actual

    # :exclude-members: None - has no effect. Unlike :members:,
    # :special-members:, etc. where None == "include all", here None means
    # "no/false/off".
    config = _AutodocConfig(
        autodoc_default_options={'members': True, 'exclude-members': True}
    )
    actual = do_autodoc('class', 'target.enums.EnumCls', config=config)
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    config = _AutodocConfig(
        autodoc_default_options={
            'members': True,
            'special-members': True,
            'exclude-members': True,
        }
    )
    actual = do_autodoc('class', 'target.CustomIter', config=config)
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert list_of_weak_references in actual
    assert '   .. py:method:: CustomIter.snafucate()' in actual
    assert '      Makes this snafucated.' in actual


def test_autodoc_default_options_with_values() -> None:
    if sys.version_info[:3] >= (3, 12, 1):
        list_of_weak_references = '      list of weak references to the object'
    else:
        list_of_weak_references = '      list of weak references to the object (if defined)'  # fmt: skip

    # with :members:
    config = _AutodocConfig(autodoc_default_options={'members': 'val1,val2'})
    actual = do_autodoc('class', 'target.enums.EnumCls', config=config)
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :member-order:
    config = _AutodocConfig(
        autodoc_default_options={'members': True, 'member-order': 'bysource'}
    )
    actual = do_autodoc('class', 'target.Class', config=config)
    assert [line for line in actual if '::' in line] == [
        '.. py:class:: Class(arg)',
        '   .. py:method:: Class.meth()',
        '   .. py:method:: Class.skipmeth()',
        '   .. py:method:: Class.excludemeth()',
        '   .. py:attribute:: Class.attr',
        '   .. py:attribute:: Class.docattr',
        '   .. py:attribute:: Class.udocattr',
        '   .. py:attribute:: Class.mdocattr',
        '   .. py:method:: Class.moore(a, e, f) -> happiness',
        '   .. py:attribute:: Class.inst_attr_inline',
        '   .. py:attribute:: Class.inst_attr_comment',
        '   .. py:attribute:: Class.inst_attr_string',
    ]

    # with :special-members:
    config = _AutodocConfig(
        autodoc_default_options={'special-members': '__init__,__iter__'}
    )
    actual = do_autodoc('class', 'target.CustomIter', config=config)
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert list_of_weak_references not in actual

    # with :exclude-members:
    config = _AutodocConfig(
        autodoc_default_options={'members': True, 'exclude-members': 'val1'}
    )
    actual = do_autodoc('class', 'target.enums.EnumCls', config=config)
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    config = _AutodocConfig(
        autodoc_default_options={
            'members': True,
            'special-members': True,
            'exclude-members': '__weakref__,snafucate',
        }
    )
    actual = do_autodoc('class', 'target.CustomIter', config=config)
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert list_of_weak_references not in actual
    assert '   .. py:method:: CustomIter.snafucate()' not in actual
    assert '      Makes this snafucated.' not in actual
