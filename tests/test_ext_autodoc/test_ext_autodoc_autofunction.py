"""Test the autodoc extension.

This tests mainly the Documenters; the auto directives are tested in a test
source file translated by test_build.
"""

from __future__ import annotations

import pytest

from tests.test_ext_autodoc.autodoc_util import do_autodoc

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


def test_callable() -> None:
    actual = do_autodoc('function', 'target.callable.function')
    assert actual == [
        '',
        '.. py:function:: function(arg1, arg2, **kwargs)',
        '   :module: target.callable',
        '',
        '   A callable object that behaves like a function.',
        '',
    ]


def test_method() -> None:
    actual = do_autodoc('function', 'target.callable.method')
    assert actual == [
        '',
        '.. py:function:: method(arg1, arg2)',
        '   :module: target.callable',
        '',
        '   docstring of Callable.method().',
        '',
    ]


def test_builtin_function() -> None:
    actual = do_autodoc('function', 'os.umask')
    assert actual == [
        '',
        '.. py:function:: umask(mask, /)',
        '   :module: os',
        '',
        '   Set the current numeric umask and return the previous umask.',
        '',
    ]


def test_methoddescriptor() -> None:
    actual = do_autodoc('function', 'builtins.int.__add__')
    assert actual == [
        '',
        '.. py:function:: __add__(self, value, /)',
        '   :module: builtins.int',
        '',
        '   Return self+value.',
        '',
    ]


def test_decorated() -> None:
    actual = do_autodoc('function', 'target.decorator.foo')
    assert actual == [
        '',
        '.. py:function:: foo(name=None, age=None)',
        '   :module: target.decorator',
        '',
    ]


def test_singledispatch() -> None:
    actual = do_autodoc('function', 'target.singledispatch.func')
    assert actual == [
        '',
        '.. py:function:: func(arg, kwarg=None)',
        '                 func(arg: float, kwarg=None)',
        '                 func(arg: int, kwarg=None)',
        '                 func(arg: str, kwarg=None)',
        '                 func(arg: dict, kwarg=None)',
        '   :module: target.singledispatch',
        '',
        '   A function for general use.',
        '',
    ]


def test_cfunction() -> None:
    actual = do_autodoc('function', 'time.asctime')
    assert actual == [
        '',
        '.. py:function:: asctime([tuple]) -> string',
        '   :module: time',
        '',
        "   Convert a time tuple to a string, e.g. 'Sat Jun 06 16:26:11 1998'.",
        '   When the time tuple is not present, current time as returned by localtime()',
        '   is used.',
        '',
    ]


def test_wrapped_function() -> None:
    actual = do_autodoc('function', 'target.wrappedfunction.slow_function')
    assert actual == [
        '',
        '.. py:function:: slow_function(message, timeout)',
        '   :module: target.wrappedfunction',
        '',
        '   This function is slow.',
        '',
    ]


def test_wrapped_function_contextmanager() -> None:
    actual = do_autodoc('function', 'target.wrappedfunction.feeling_good')
    assert actual == [
        '',
        '.. py:function:: feeling_good(x: int, y: int) -> ~typing.Generator',
        '   :module: target.wrappedfunction',
        '',
        "   You'll feel better in this context!",
        '',
    ]


def test_coroutine() -> None:
    actual = do_autodoc('function', 'target.functions.coroutinefunc')
    assert actual == [
        '',
        '.. py:function:: coroutinefunc()',
        '   :module: target.functions',
        '   :async:',
        '',
    ]


def test_synchronized_coroutine() -> None:
    actual = do_autodoc('function', 'target.coroutine.sync_func')
    assert actual == [
        '',
        '.. py:function:: sync_func()',
        '   :module: target.coroutine',
        '',
    ]


def test_async_generator() -> None:
    actual = do_autodoc('function', 'target.functions.asyncgenerator')
    assert actual == [
        '',
        '.. py:function:: asyncgenerator()',
        '   :module: target.functions',
        '   :async:',
        '',
    ]


def test_slice_function_arg() -> None:
    actual = do_autodoc('function', 'target.functions.slice_arg_func')
    assert actual == [
        '',
        '.. py:function:: slice_arg_func(arg: float64[:, :])',
        '   :module: target.functions',
        '',
    ]
