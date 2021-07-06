"""
    test_ext_autodoc_configs
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly for config variables

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import platform
import sys

import pytest

from sphinx.testing import restructuredtext

from .test_ext_autodoc import do_autodoc

IS_PYPY = platform.python_implementation() == 'PyPy'


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_class(app):
    app.config.autoclass_content = 'class'
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.autoclass_content', options)
    assert list(actual) == [
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_init(app):
    app.config.autoclass_content = 'init'
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.autoclass_content', options)
    assert list(actual) == [
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_signature_mixed(app):
    app.config.autodoc_class_signature = 'mixed'
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'class', 'target.classes.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar(x, y)',
        '   :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_signature_separated_init(app):
    app.config.autodoc_class_signature = 'separated'
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'class', 'target.classes.Bar', options)
    assert list(actual) == [
        '',
        '.. py:class:: Bar',
        '   :module: target.classes',
        '',
        '',
        '   .. py:method:: Bar.__init__(x, y)',
        '      :module: target.classes',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_class_signature_separated_new(app):
    app.config.autodoc_class_signature = 'separated'
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'class', 'target.classes.Baz', options)
    assert list(actual) == [
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_both(app):
    app.config.autoclass_content = 'both'
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.autoclass_content', options)
    assert list(actual) == [
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_inherit_docstrings(app):
    assert app.config.autodoc_inherit_docstrings is True  # default
    actual = do_autodoc(app, 'method', 'target.inheritance.Derived.inheritedmeth')
    assert list(actual) == [
        '',
        '.. py:method:: Derived.inheritedmeth()',
        '   :module: target.inheritance',
        '',
        '   Inherited function.',
        '',
    ]

    # disable autodoc_inherit_docstrings
    app.config.autodoc_inherit_docstrings = False
    actual = do_autodoc(app, 'method', 'target.inheritance.Derived.inheritedmeth')
    assert list(actual) == [
        '',
        '.. py:method:: Derived.inheritedmeth()',
        '   :module: target.inheritance',
        ''
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_docstring_signature(app):
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        '',
        '.. py:class:: DocstringSig()',
        '   :module: target',
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
    app.config.autodoc_docstring_signature = False
    actual = do_autodoc(app, 'class', 'target.DocstringSig', options)
    assert list(actual) == [
        '',
        '.. py:class:: DocstringSig()',
        '   :module: target',
        '',
        '',
        '   .. py:method:: DocstringSig.meth()',
        '      :module: target',
        '',
        '      meth(FOO, BAR=1) -> BAZ',
        '      First line of docstring',
        '',
        '              rest of docstring',
        '',
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_and_docstring_signature_class(app):
    app.config.autoclass_content = 'class'
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'target.docstring_signature', options)
    assert list(actual) == [
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


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_and_docstring_signature_init(app):
    app.config.autoclass_content = 'init'
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'target.docstring_signature', options)
    assert list(actual) == [
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
        '.. py:class:: E(foo: int, bar: int, baz: int) -> None',
        '              E(foo: str, bar: str, baz: str) -> None',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F(foo: int, bar: int, baz: int) -> None',
        '              F(foo: str, bar: str, baz: str) -> None',
        '   :module: target.docstring_signature',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autoclass_content_and_docstring_signature_both(app):
    app.config.autoclass_content = 'both'
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'target.docstring_signature', options)
    assert list(actual) == [
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
        '.. py:class:: E(foo: int, bar: int, baz: int) -> None',
        '              E(foo: str, bar: str, baz: str) -> None',
        '   :module: target.docstring_signature',
        '',
        '',
        '.. py:class:: F(foo: int, bar: int, baz: int) -> None',
        '              F(foo: str, bar: str, baz: str) -> None',
        '   :module: target.docstring_signature',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
@pytest.mark.usefixtures("rollback_sysmodules")
def test_mocked_module_imports(app, warning):
    sys.modules.pop('target', None)  # unload target module to clear the module cache

    # no autodoc_mock_imports
    options = {"members": 'TestAutodoc,decoratedFunction,func'}
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert list(actual) == []
    assert "autodoc: failed to import module 'need_mocks'" in warning.getvalue()

    # with autodoc_mock_imports
    app.config.autodoc_mock_imports = [
        'missing_module',
        'missing_package1',
        'missing_package2',
        'missing_package3',
        'sphinx.missing_module4',
    ]

    warning.truncate(0)
    actual = do_autodoc(app, 'module', 'target.need_mocks', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.need_mocks',
        '',
        '',
        '.. py:class:: TestAutodoc()',
        '   :module: target.need_mocks',
        '',
        '   TestAutodoc docstring.',
        '',
        '',
        '   .. py:method:: TestAutodoc.decoratedMethod()',
        '      :module: target.need_mocks',
        '',
        '      TestAutodoc::decoratedMethod docstring',
        '',
        '',
        '.. py:function:: decoratedFunction()',
        '   :module: target.need_mocks',
        '',
        '   decoratedFunction docstring',
        '',
        '',
        '.. py:function:: func(arg: missing_module.Class)',
        '   :module: target.need_mocks',
        '',
        '   a function takes mocked object as an argument',
        '',
    ]
    assert warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "signature"})
def test_autodoc_typehints_signature(app):
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '   :type: int',
        '',
        '',
        '.. py:class:: Math(s: str, o: Optional[Any] = None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :type: int',
        '      :value: 1',
        '',
        '',
        '   .. py:method:: Math.decr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a: str, b: int) -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a: int, b: int = 1) -> int',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing() -> None',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '      :type: int',
        '',
        '',
        '.. py:class:: NewAnnotation(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a: int)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: complex_func(arg1: str, arg2: List[int], arg3: Tuple[int, '
        'Union[str, Unknown]] = None, *args: str, **kwargs: str) -> None',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a: int, b: int = 1) -> int',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a: str, b: Optional[str] = None) -> str',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x: Tuple[int, Union[int, str]]) -> Tuple[int, int]',
        '   :module: target.typehints',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "none"})
def test_autodoc_typehints_none(app):
    options = {"members": None,
               "undoc-members": None}
    actual = do_autodoc(app, 'module', 'target.typehints', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.typehints',
        '',
        '',
        '.. py:data:: CONST1',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: Math(s, o=None)',
        '   :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST1',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:attribute:: Math.CONST2',
        '      :module: target.typehints',
        '      :value: 1',
        '',
        '',
        '   .. py:method:: Math.decr(a, b=1)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.horse(a, b)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.incr(a, b=1)',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:method:: Math.nothing()',
        '      :module: target.typehints',
        '',
        '',
        '   .. py:property:: Math.prop',
        '      :module: target.typehints',
        '',
        '',
        '.. py:class:: NewAnnotation(i)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: NewComment(i)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:class:: SignatureFromMetaclass(a)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: complex_func(arg1, arg2, arg3=None, *args, **kwargs)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: decr(a, b=1)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: incr(a, b=1)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: missing_attr(c, a, b=None)',
        '   :module: target.typehints',
        '',
        '',
        '.. py:function:: tuple_args(x)',
        '   :module: target.typehints',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': 'none'})
def test_autodoc_typehints_none_for_overload(app):
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.overload', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.overload',
        '',
        '',
        '.. py:class:: Bar(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Baz(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Foo(x, y)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '.. py:class:: Math()',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
        '',
        '   .. py:method:: Math.sum(x, y=None)',
        '      :module: target.overload',
        '',
        '      docstring',
        '',
        '',
        '.. py:function:: sum(x, y=None)',
        '   :module: target.overload',
        '',
        '   docstring',
        '',
    ]


@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "description"})
def test_autodoc_typehints_description(app):
    app.build()
    context = (app.outdir / 'index.txt').read_text()
    assert ('target.typehints.incr(a, b=1)\n'
            '\n'
            '   Parameters:\n'
            '      * **a** (*int*) --\n'
            '\n'
            '      * **b** (*int*) --\n'
            '\n'
            '   Return type:\n'
            '      int\n'
            in context)
    assert ('target.typehints.tuple_args(x)\n'
            '\n'
            '   Parameters:\n'
            '      **x** (*Tuple**[**int**, **Union**[**int**, **str**]**]*) --\n'
            '\n'
            '   Return type:\n'
            '      Tuple[int, int]\n'
            in context)

    # Overloads still get displyed in the signature
    assert ('target.overload.sum(x: int, y: int = 0) -> int\n'
            'target.overload.sum(x: float, y: float = 0.0) -> float\n'
            'target.overload.sum(x: str, y: str = None) -> str\n'
            '\n'
            '   docstring\n'
            in context)


@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "description",
                                   'autodoc_typehints_description_target': 'documented'})
def test_autodoc_typehints_description_no_undoc(app):
    # No :type: or :rtype: will be injected for `incr`, which does not have
    # a description for its parameters or its return. `tuple_args` does
    # describe them, so :type: and :rtype: will be added.
    (app.srcdir / 'index.rst').write_text(
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '   :param x: arg\n'
        '   :return: another tuple\n'
    )
    app.build()
    context = (app.outdir / 'index.txt').read_text()
    assert ('target.typehints.incr(a, b=1)\n'
            '\n'
            'target.typehints.tuple_args(x)\n'
            '\n'
            '   Parameters:\n'
            '      **x** (*Tuple**[**int**, **Union**[**int**, **str**]**]*) -- arg\n'
            '\n'
            '   Returns:\n'
            '      another tuple\n'
            '\n'
            '   Return type:\n'
            '      Tuple[int, int]\n'
            in context)


@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "description"})
def test_autodoc_typehints_description_with_documented_init(app):
    (app.srcdir / 'index.rst').write_text(
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n'
    )
    app.build()
    context = (app.outdir / 'index.txt').read_text()
    assert ('class target.typehints._ClassWithDocumentedInit(x)\n'
            '\n'
            '   Class docstring.\n'
            '\n'
            '   Parameters:\n'
            '      **x** (*int*) --\n'
            '\n'
            '   Return type:\n'
            '      None\n'
            '\n'
            '   __init__(x)\n'
            '\n'
            '      Init docstring.\n'
            '\n'
            '      Parameters:\n'
            '         **x** (*int*) -- Some integer\n'
            '\n'
            '      Return type:\n'
            '         None\n' == context)


@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "description",
                                   'autodoc_typehints_description_target': 'documented'})
def test_autodoc_typehints_description_with_documented_init_no_undoc(app):
    (app.srcdir / 'index.rst').write_text(
        '.. autoclass:: target.typehints._ClassWithDocumentedInit\n'
        '   :special-members: __init__\n'
    )
    app.build()
    context = (app.outdir / 'index.txt').read_text()
    assert ('class target.typehints._ClassWithDocumentedInit(x)\n'
            '\n'
            '   Class docstring.\n'
            '\n'
            '   __init__(x)\n'
            '\n'
            '      Init docstring.\n'
            '\n'
            '      Parameters:\n'
            '         **x** (*int*) -- Some integer\n' == context)


@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "description"})
def test_autodoc_typehints_description_for_invalid_node(app):
    text = ".. py:function:: hello; world"
    restructuredtext.parse(app, text)  # raises no error


@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    confoverrides={'autodoc_typehints': "both"})
def test_autodoc_typehints_both(app):
    (app.srcdir / 'index.rst').write_text(
        '.. autofunction:: target.typehints.incr\n'
        '\n'
        '.. autofunction:: target.typehints.tuple_args\n'
        '\n'
        '.. autofunction:: target.overload.sum\n'
    )
    app.build()
    context = (app.outdir / 'index.txt').read_text()
    assert ('target.typehints.incr(a: int, b: int = 1) -> int\n'
            '\n'
            '   Parameters:\n'
            '      * **a** (*int*) --\n'
            '\n'
            '      * **b** (*int*) --\n'
            '\n'
            '   Return type:\n'
            '      int\n'
            in context)
    assert ('target.typehints.tuple_args(x: Tuple[int, Union[int, str]]) -> Tuple[int, int]\n'
            '\n'
            '   Parameters:\n'
            '      **x** (*Tuple**[**int**, **Union**[**int**, **str**]**]*) --\n'
            '\n'
            '   Return type:\n'
            '      Tuple[int, int]\n'
            in context)

    # Overloads still get displyed in the signature
    assert ('target.overload.sum(x: int, y: int = 0) -> int\n'
            'target.overload.sum(x: float, y: float = 0.0) -> float\n'
            'target.overload.sum(x: str, y: str = None) -> str\n'
            '\n'
            '   docstring\n'
            in context)


@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required.')
@pytest.mark.sphinx('text', testroot='ext-autodoc')
def test_autodoc_type_aliases(app):
    # default
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.autodoc_type_aliases', options)
    assert list(actual) == [
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
        '.. py:function:: read(r: _io.BytesIO) -> _io.StringIO',
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
    ]

    # define aliases
    app.config.autodoc_type_aliases = {'myint': 'myint',
                                       'io.StringIO': 'my.module.StringIO'}
    actual = do_autodoc(app, 'module', 'target.autodoc_type_aliases', options)
    assert list(actual) == [
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
        '.. py:function:: read(r: _io.BytesIO) -> my.module.StringIO',
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
    ]


@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required.')
@pytest.mark.sphinx('text', testroot='ext-autodoc',
                    srcdir='autodoc_typehints_description_and_type_aliases',
                    confoverrides={'autodoc_typehints': "description",
                                   'autodoc_type_aliases': {'myint': 'myint'}})
def test_autodoc_typehints_description_and_type_aliases(app):
    (app.srcdir / 'autodoc_type_aliases.rst').write_text('.. autofunction:: target.autodoc_type_aliases.sum')
    app.build()
    context = (app.outdir / 'autodoc_type_aliases.txt').read_text()
    assert ('target.autodoc_type_aliases.sum(x, y)\n'
            '\n'
            '   docstring\n'
            '\n'
            '   Parameters:\n'
            '      * **x** (*myint*) --\n'
            '\n'
            '      * **y** (*myint*) --\n'
            '\n'
            '   Return type:\n'
            '      myint\n' == context)


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options(app):
    # no settings
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: target.CustomIter' not in actual
    actual = do_autodoc(app, 'module', 'target')
    assert '.. py:function:: save_traceback(app)' not in actual

    # with :members:
    app.config.autodoc_default_options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: = True
    app.config.autodoc_default_options = {'members': None}
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :members: and :undoc-members:
    app.config.autodoc_default_options = {
        'members': None,
        'undoc-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' in actual

    # with :special-members:
    # Note that :members: must be *on* for :special-members: to work.
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert '      list of weak references to the object (if defined)' in actual

    # :exclude-members: None - has no effect. Unlike :members:,
    # :special-members:, etc. where None == "include all", here None means
    # "no/false/off".
    app.config.autodoc_default_options = {
        'members': None,
        'exclude-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
        'exclude-members': None,
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' in actual
        assert '      list of weak references to the object (if defined)' in actual
    assert '   .. py:method:: CustomIter.snafucate()' in actual
    assert '      Makes this snafucated.' in actual


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_autodoc_default_options_with_values(app):
    # with :members:
    app.config.autodoc_default_options = {'members': 'val1,val2'}
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' not in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual

    # with :member-order:
    app.config.autodoc_default_options = {
        'members': None,
        'member-order': 'bysource',
    }
    actual = do_autodoc(app, 'class', 'target.Class')
    assert list(filter(lambda l: '::' in l, actual)) == [
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
    app.config.autodoc_default_options = {
        'special-members': '__init__,__iter__',
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert '      list of weak references to the object (if defined)' not in actual

    # with :exclude-members:
    app.config.autodoc_default_options = {
        'members': None,
        'exclude-members': 'val1'
    }
    actual = do_autodoc(app, 'class', 'target.enums.EnumCls')
    assert '   .. py:attribute:: EnumCls.val1' not in actual
    assert '   .. py:attribute:: EnumCls.val2' in actual
    assert '   .. py:attribute:: EnumCls.val3' in actual
    assert '   .. py:attribute:: EnumCls.val4' not in actual
    app.config.autodoc_default_options = {
        'members': None,
        'special-members': None,
        'exclude-members': '__weakref__,snafucate',
    }
    actual = do_autodoc(app, 'class', 'target.CustomIter')
    assert '   .. py:method:: CustomIter.__init__()' in actual
    assert '      Create a new `CustomIter`.' in actual
    assert '   .. py:method:: CustomIter.__iter__()' in actual
    assert '      Iterate squares of each value.' in actual
    if not IS_PYPY:
        assert '   .. py:attribute:: CustomIter.__weakref__' not in actual
        assert '      list of weak references to the object (if defined)' not in actual
    assert '   .. py:method:: CustomIter.snafucate()' not in actual
    assert '      Makes this snafucated.' not in actual
