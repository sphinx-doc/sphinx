"""
    test_ext_autodoc_autofunction
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.  This tests mainly the Documenters; the auto
    directives are tested in a test source file translated by test_build.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

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
def test_callable(app):
    actual = do_autodoc(app, 'function', 'target.callable.function')
    assert list(actual) == [
        '',
        '.. py:function:: function(arg1, arg2, **kwargs)',
        '   :module: target.callable',
        '',
        '   A callable object that behaves like a function.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_method(app):
    actual = do_autodoc(app, 'function', 'target.callable.method')
    assert list(actual) == [
        '',
        '.. py:function:: method(arg1, arg2)',
        '   :module: target.callable',
        '',
        '   docstring of Callable.method().',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_builtin_function(app):
    actual = do_autodoc(app, 'function', 'os.umask')
    assert list(actual) == [
        '',
        '.. py:function:: umask(mask, /)',
        '   :module: os',
        '',
        '   Set the current numeric umask and return the previous umask.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_methoddescriptor(app):
    actual = do_autodoc(app, 'function', 'builtins.int.__add__')
    assert list(actual) == [
        '',
        '.. py:function:: __add__(self, value, /)',
        '   :module: builtins.int',
        '',
        '   Return self+value.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_decorated(app):
    actual = do_autodoc(app, 'function', 'target.decorator.foo')
    assert list(actual) == [
        '',
        '.. py:function:: foo(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_singledispatch(app):
    options = {}
    actual = do_autodoc(app, 'function', 'target.singledispatch.func', options)
    assert list(actual) == [
        '',
        '.. py:function:: func(arg, kwarg=None)',
        '                 func(arg: float, kwarg=None)',
        '                 func(arg: int, kwarg=None)',
        '                 func(arg: str, kwarg=None)',
        '   :module: target.singledispatch',
        '',
        '   A function for general use.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_cfunction(app):
    actual = do_autodoc(app, 'function', 'time.asctime')
    assert list(actual) == [
        '',
        '.. py:function:: asctime([tuple]) -> string',
        '   :module: time',
        '',
        "   Convert a time tuple to a string, e.g. 'Sat Jun 06 16:26:11 1998'.",
        '   When the time tuple is not present, current time as returned by localtime()',
        '   is used.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_wrapped_function(app):
    actual = do_autodoc(app, 'function', 'target.wrappedfunction.slow_function')
    assert list(actual) == [
        '',
        '.. py:function:: slow_function(message, timeout)',
        '   :module: target.wrappedfunction',
        '',
        '   This function is slow.',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_wrapped_function_contextmanager(app):
    actual = do_autodoc(app, 'function', 'target.wrappedfunction.feeling_good')
    assert list(actual) == [
        '',
        '.. py:function:: feeling_good(x: int, y: int) -> Generator',
        '   :module: target.wrappedfunction',
        '',
        "   You'll feel better in this context!",
        '',
    ]
