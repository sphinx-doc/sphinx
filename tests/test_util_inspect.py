# -*- coding: utf-8 -*-
"""
    test_util_inspect
    ~~~~~~~~~~~~~~~

    Tests util.inspect functions.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys
from six import PY3
import functools
from textwrap import dedent
import pytest

from sphinx.util import inspect


def test_getargspec():
    def func(a, b, c=1, d=2, *e, **f):
        pass

    spec = inspect.getargspec(func)
    assert spec.args == ['a', 'b', 'c', 'd']
    assert spec.varargs == 'e'
    if PY3:
        assert spec.varkw == 'f'
        assert spec.defaults == (1, 2)
        assert spec.kwonlyargs == []
        assert spec.kwonlydefaults is None
        assert spec.annotations == {}
    else:
        assert spec.keywords == 'f'
        assert spec.defaults == [1, 2]


def test_getargspec_partial():
    def func1(a, b, c=1, d=2, *e, **f):
        pass

    partial = functools.partial(func1, 10, c=11)
    spec = inspect.getargspec(partial)
    if PY3:
        assert spec.args == ['b']
        assert spec.varargs is None
        assert spec.varkw == 'f'
        assert spec.defaults is None
        assert spec.kwonlyargs == ['c', 'd']
        assert spec.kwonlydefaults == {'c': 11, 'd': 2}
        assert spec.annotations == {}
    else:
        assert spec.args == ['b', 'd']
        assert spec.varargs == 'e'
        assert spec.keywords == 'f'
        assert spec.defaults == [2]


def test_getargspec_partial2():
    def fun(a, b, c=1, d=2):
        pass
    p = functools.partial(fun, 10, c=11)

    if PY3:
        # Python 3's partial is rather cleverer than Python 2's, and we
        # have to jump through some hoops to define an equivalent function
        # in a way that won't confuse Python 2's parser:
        ns = {}
        exec(dedent("""
            def f_expected(b, *, c=11, d=2):
                    pass
        """), ns)
        f_expected = ns["f_expected"]
    else:
        def f_expected(b, d=2):
            pass
    expected = inspect.getargspec(f_expected)

    assert expected == inspect.getargspec(p)


def test_getargspec_builtin_type():
    with pytest.raises(TypeError):
        inspect.getargspec(int)


def test_getargspec_bound_methods():
    def f_expected_unbound(self, arg1, **kwargs):
        pass
    expected_unbound = inspect.getargspec(f_expected_unbound)

    def f_expected_bound(arg1, **kwargs):
        pass
    expected_bound = inspect.getargspec(f_expected_bound)

    class Foo:
        def method(self, arg1, **kwargs):
            pass

    bound_method = Foo().method

    @functools.wraps(bound_method)
    def wrapped_bound_method(*args, **kwargs):
        pass

    assert expected_unbound == inspect.getargspec(Foo.method)
    if PY3 and sys.version_info >= (3, 4, 4):
        # On py2, the inspect functions don't properly handle bound
        # methods (they include a spurious 'self' argument)
        assert expected_bound == inspect.getargspec(bound_method)
        # On py2, the inspect functions can't properly handle wrapped
        # functions (no __wrapped__ support)
        assert expected_bound == inspect.getargspec(wrapped_bound_method)


def test_safe_getattr_with_default():
    class Foo(object):
        def __getattr__(self, item):
            raise Exception

    obj = Foo()

    result = inspect.safe_getattr(obj, 'bar', 'baz')

    assert result == 'baz'


def test_safe_getattr_with_exception():
    class Foo(object):
        def __getattr__(self, item):
            raise Exception

    obj = Foo()

    try:
        inspect.safe_getattr(obj, 'bar')
    except AttributeError as exc:
        assert exc.args[0] == 'bar'
    else:
        pytest.fail('AttributeError not raised')


def test_safe_getattr_with_property_exception():
    class Foo(object):
        @property
        def bar(self):
            raise Exception

    obj = Foo()

    try:
        inspect.safe_getattr(obj, 'bar')
    except AttributeError as exc:
        assert exc.args[0] == 'bar'
    else:
        pytest.fail('AttributeError not raised')


def test_safe_getattr_with___dict___override():
    class Foo(object):
        @property
        def __dict__(self):
            raise Exception

    obj = Foo()

    try:
        inspect.safe_getattr(obj, 'bar')
    except AttributeError as exc:
        assert exc.args[0] == 'bar'
    else:
        pytest.fail('AttributeError not raised')
