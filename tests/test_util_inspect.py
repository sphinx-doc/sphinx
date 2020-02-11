"""
    test_util_inspect
    ~~~~~~~~~~~~~~~

    Tests util.inspect functions.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import _testcapi
import datetime
import functools
import sys
import types

import pytest

from sphinx.util import inspect
from sphinx.util.inspect import stringify_signature


def test_getargspec():
    def func(a, b, c=1, d=2, *e, **f):
        pass

    spec = inspect.getargspec(func)
    assert spec.args == ['a', 'b', 'c', 'd']
    assert spec.varargs == 'e'
    assert spec.varkw == 'f'
    assert spec.defaults == (1, 2)
    assert spec.kwonlyargs == []
    assert spec.kwonlydefaults is None
    assert spec.annotations == {}


def test_getargspec_partial():
    def func1(a, b, c=1, d=2, *e, **f):
        pass

    partial = functools.partial(func1, 10, c=11)
    spec = inspect.getargspec(partial)
    assert spec.args == ['b']
    assert spec.varargs is None
    assert spec.varkw == 'f'
    assert spec.defaults is None
    assert spec.kwonlyargs == ['c', 'd']
    assert spec.kwonlydefaults == {'c': 11, 'd': 2}
    assert spec.annotations == {}


def test_getargspec_partial2():
    def fun(a, b, c=1, d=2):
        pass
    p = functools.partial(fun, 10, c=11)

    def f_expected(b, *, c=11, d=2):
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
    assert expected_bound == inspect.getargspec(bound_method)
    assert expected_bound == inspect.getargspec(wrapped_bound_method)


def test_signature():
    # literals
    with pytest.raises(TypeError):
        inspect.signature(1)

    with pytest.raises(TypeError):
        inspect.signature('')

    # builitin classes
    with pytest.raises(TypeError):
        inspect.signature(int)

    with pytest.raises(TypeError):
        inspect.signature(str)

    # normal function
    def func(a, b, c=1, d=2, *e, **f):
        pass

    sig = inspect.stringify_signature(inspect.signature(func))
    assert sig == '(a, b, c=1, d=2, *e, **f)'


def test_signature_partial():
    def fun(a, b, c=1, d=2):
        pass
    p = functools.partial(fun, 10, c=11)

    sig = inspect.signature(p)
    assert stringify_signature(sig) == '(b, *, c=11, d=2)'


def test_signature_methods():
    class Foo:
        def meth1(self, arg1, **kwargs):
            pass

        @classmethod
        def meth2(cls, arg1, *args, **kwargs):
            pass

        @staticmethod
        def meth3(arg1, *args, **kwargs):
            pass

    @functools.wraps(Foo().meth1)
    def wrapped_bound_method(*args, **kwargs):
        pass

    # unbound method
    sig = inspect.signature(Foo.meth1)
    assert stringify_signature(sig) == '(self, arg1, **kwargs)'

    sig = inspect.signature(Foo.meth1, bound_method=True)
    assert stringify_signature(sig) == '(arg1, **kwargs)'

    # bound method
    sig = inspect.signature(Foo().meth1)
    assert stringify_signature(sig) == '(arg1, **kwargs)'

    # class method
    sig = inspect.signature(Foo.meth2)
    assert stringify_signature(sig) == '(arg1, *args, **kwargs)'

    sig = inspect.signature(Foo().meth2)
    assert stringify_signature(sig) == '(arg1, *args, **kwargs)'

    # static method
    sig = inspect.signature(Foo.meth3)
    assert stringify_signature(sig) == '(arg1, *args, **kwargs)'

    sig = inspect.signature(Foo().meth3)
    assert stringify_signature(sig) == '(arg1, *args, **kwargs)'

    # wrapped bound method
    sig = inspect.signature(wrapped_bound_method)
    assert stringify_signature(sig) == '(arg1, **kwargs)'


def test_signature_partialmethod():
    from functools import partialmethod

    class Foo:
        def meth1(self, arg1, arg2, arg3=None, arg4=None):
            pass

        def meth2(self, arg1, arg2):
            pass

        foo = partialmethod(meth1, 1, 2)
        bar = partialmethod(meth1, 1, arg3=3)
        baz = partialmethod(meth2, 1, 2)

    subject = Foo()
    sig = inspect.signature(subject.foo)
    assert stringify_signature(sig) == '(arg3=None, arg4=None)'

    sig = inspect.signature(subject.bar)
    assert stringify_signature(sig) == '(arg2, *, arg3=3, arg4=None)'

    sig = inspect.signature(subject.baz)
    assert stringify_signature(sig) == '()'


def test_signature_annotations():
    from typing_test_data import (f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10,
                                  f11, f12, f13, f14, f15, f16, f17, f18, f19, Node)

    # Class annotations
    sig = inspect.signature(f0)
    assert stringify_signature(sig) == '(x: int, y: numbers.Integral) -> None'

    # Generic types with concrete parameters
    sig = inspect.signature(f1)
    assert stringify_signature(sig) == '(x: List[int]) -> List[int]'

    # TypeVars and generic types with TypeVars
    sig = inspect.signature(f2)
    assert stringify_signature(sig) == '(x: List[T], y: List[T_co], z: T) -> List[T_contra]'

    # Union types
    sig = inspect.signature(f3)
    assert stringify_signature(sig) == '(x: Union[str, numbers.Integral]) -> None'

    # Quoted annotations
    sig = inspect.signature(f4)
    assert stringify_signature(sig) == '(x: str, y: str) -> None'

    # Keyword-only arguments
    sig = inspect.signature(f5)
    assert stringify_signature(sig) == '(x: int, *, y: str, z: str) -> None'

    # Keyword-only arguments with varargs
    sig = inspect.signature(f6)
    assert stringify_signature(sig) == '(x: int, *args, y: str, z: str) -> None'

    # Space around '=' for defaults
    sig = inspect.signature(f7)
    assert stringify_signature(sig) == '(x: int = None, y: dict = {}) -> None'

    # Callable types
    sig = inspect.signature(f8)
    assert stringify_signature(sig) == '(x: Callable[[int, str], int]) -> None'

    sig = inspect.signature(f9)
    assert stringify_signature(sig) == '(x: Callable) -> None'

    # Tuple types
    sig = inspect.signature(f10)
    assert stringify_signature(sig) == '(x: Tuple[int, str], y: Tuple[int, ...]) -> None'

    # Instance annotations
    sig = inspect.signature(f11)
    assert stringify_signature(sig) == '(x: CustomAnnotation, y: 123) -> None'

    # tuple with more than two items
    sig = inspect.signature(f12)
    assert stringify_signature(sig) == '() -> Tuple[int, str, int]'

    # optional
    sig = inspect.signature(f13)
    assert stringify_signature(sig) == '() -> Optional[str]'

    # Any
    sig = inspect.signature(f14)
    assert stringify_signature(sig) == '() -> Any'

    # ForwardRef
    sig = inspect.signature(f15)
    assert stringify_signature(sig) == '(x: Unknown, y: int) -> Any'

    # keyword only arguments (1)
    sig = inspect.signature(f16)
    assert stringify_signature(sig) == '(arg1, arg2, *, arg3=None, arg4=None)'

    # keyword only arguments (2)
    sig = inspect.signature(f17)
    assert stringify_signature(sig) == '(*, arg3, arg4)'

    sig = inspect.signature(f18)
    assert stringify_signature(sig) == '(self, arg1: Union[int, Tuple] = 10) -> List[Dict]'

    # annotations for variadic and keyword parameters
    sig = inspect.signature(f19)
    assert stringify_signature(sig) == '(*args: int, **kwargs: str)'

    # type hints by string
    sig = inspect.signature(Node.children)
    if (3, 5, 0) <= sys.version_info < (3, 5, 3):
        assert stringify_signature(sig) == '(self) -> List[Node]'
    else:
        assert stringify_signature(sig) == '(self) -> List[typing_test_data.Node]'

    sig = inspect.signature(Node.__init__)
    assert stringify_signature(sig) == '(self, parent: Optional[Node]) -> None'

    # show_annotation is False
    sig = inspect.signature(f7)
    assert stringify_signature(sig, show_annotation=False) == '(x=None, y={})'

    # show_return_annotation is False
    sig = inspect.signature(f7)
    assert stringify_signature(sig, show_return_annotation=False) == '(x: int = None, y: dict = {})'


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
@pytest.mark.sphinx(testroot='ext-autodoc')
def test_signature_annotations_py38(app):
    from target.pep570 import foo, bar

    # case: separator in the middle
    sig = inspect.signature(foo)
    assert stringify_signature(sig) == '(a, b, /, c, d)'

    # case: separator at tail
    sig = inspect.signature(bar)
    assert stringify_signature(sig) == '(a, b, /)'


def test_safe_getattr_with_default():
    class Foo:
        def __getattr__(self, item):
            raise Exception

    obj = Foo()

    result = inspect.safe_getattr(obj, 'bar', 'baz')

    assert result == 'baz'


def test_safe_getattr_with_exception():
    class Foo:
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
    class Foo:
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
    class Foo:
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


def test_dictionary_sorting():
    dictionary = {"c": 3, "a": 1, "d": 2, "b": 4}
    description = inspect.object_description(dictionary)
    assert description == "{'a': 1, 'b': 4, 'c': 3, 'd': 2}"


def test_set_sorting():
    set_ = set("gfedcba")
    description = inspect.object_description(set_)
    assert description == "{'a', 'b', 'c', 'd', 'e', 'f', 'g'}"


def test_set_sorting_fallback():
    set_ = {None, 1}
    description = inspect.object_description(set_)
    assert description in ("{1, None}", "{None, 1}")


def test_frozenset_sorting():
    frozenset_ = frozenset("gfedcba")
    description = inspect.object_description(frozenset_)
    assert description == "frozenset({'a', 'b', 'c', 'd', 'e', 'f', 'g'})"


def test_frozenset_sorting_fallback():
    frozenset_ = frozenset((None, 1))
    description = inspect.object_description(frozenset_)
    assert description in ("frozenset({1, None})", "frozenset({None, 1})")


def test_dict_customtype():
    class CustomType:
        def __init__(self, value):
            self._value = value

        def __repr__(self):
            return "<CustomType(%r)>" % self._value

    dictionary = {CustomType(2): 2, CustomType(1): 1}
    description = inspect.object_description(dictionary)
    # Type is unsortable, just check that it does not crash
    assert "<CustomType(2)>: 2" in description


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isstaticmethod(app):
    from target.methods import Base, Inherited

    assert inspect.isstaticmethod(Base.staticmeth, Base, 'staticmeth') is True
    assert inspect.isstaticmethod(Base.meth, Base, 'meth') is False
    assert inspect.isstaticmethod(Inherited.staticmeth, Inherited, 'staticmeth') is True
    assert inspect.isstaticmethod(Inherited.meth, Inherited, 'meth') is False


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_iscoroutinefunction(app):
    from target.functions import coroutinefunc, func, partial_coroutinefunc
    from target.methods import Base

    assert inspect.iscoroutinefunction(func) is False                   # function
    assert inspect.iscoroutinefunction(coroutinefunc) is True           # coroutine
    assert inspect.iscoroutinefunction(partial_coroutinefunc) is True   # partial-ed coroutine
    assert inspect.iscoroutinefunction(Base.meth) is False              # method
    assert inspect.iscoroutinefunction(Base.coroutinemeth) is True      # coroutine-method

    # partial-ed coroutine-method
    partial_coroutinemeth = Base.__dict__['partial_coroutinemeth']
    assert inspect.iscoroutinefunction(partial_coroutinemeth) is True


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isfunction(app):
    from target.functions import builtin_func, partial_builtin_func
    from target.functions import func, partial_func
    from target.methods import Base

    assert inspect.isfunction(func) is True                     # function
    assert inspect.isfunction(partial_func) is True             # partial-ed function
    assert inspect.isfunction(Base.meth) is True                # method of class
    assert inspect.isfunction(Base.partialmeth) is True         # partial-ed method of class
    assert inspect.isfunction(Base().meth) is False             # method of instance
    assert inspect.isfunction(builtin_func) is False            # builtin function
    assert inspect.isfunction(partial_builtin_func) is False    # partial-ed builtin function


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isbuiltin(app):
    from target.functions import builtin_func, partial_builtin_func
    from target.functions import func, partial_func
    from target.methods import Base

    assert inspect.isbuiltin(builtin_func) is True          # builtin function
    assert inspect.isbuiltin(partial_builtin_func) is True  # partial-ed builtin function
    assert inspect.isbuiltin(func) is False                 # function
    assert inspect.isbuiltin(partial_func) is False         # partial-ed function
    assert inspect.isbuiltin(Base.meth) is False            # method of class
    assert inspect.isbuiltin(Base().meth) is False          # method of instance


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isdescriptor(app):
    from target.functions import func
    from target.methods import Base

    assert inspect.isdescriptor(Base.prop) is True      # property of class
    assert inspect.isdescriptor(Base().prop) is False   # property of instance
    assert inspect.isdescriptor(Base.meth) is True      # method of class
    assert inspect.isdescriptor(Base().meth) is True    # method of instance
    assert inspect.isdescriptor(func) is True           # function


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isattributedescriptor(app):
    from target.methods import Base

    class Descriptor:
        def __get__(self, obj, typ=None):
            pass

    testinstancemethod = _testcapi.instancemethod(str.__repr__)

    assert inspect.isattributedescriptor(Base.prop) is True                    # property
    assert inspect.isattributedescriptor(Base.meth) is False                   # method
    assert inspect.isattributedescriptor(Base.staticmeth) is False             # staticmethod
    assert inspect.isattributedescriptor(Base.classmeth) is False              # classmetho
    assert inspect.isattributedescriptor(Descriptor) is False                  # custom descriptor class    # NOQA
    assert inspect.isattributedescriptor(str.join) is False                    # MethodDescriptorType       # NOQA
    assert inspect.isattributedescriptor(object.__init__) is False             # WrapperDescriptorType      # NOQA
    assert inspect.isattributedescriptor(dict.__dict__['fromkeys']) is False   # ClassMethodDescriptorType  # NOQA
    assert inspect.isattributedescriptor(types.FrameType.f_locals) is True     # GetSetDescriptorType       # NOQA
    assert inspect.isattributedescriptor(datetime.timedelta.days) is True      # MemberDescriptorType       # NOQA
    assert inspect.isattributedescriptor(testinstancemethod) is False          # instancemethod (C-API)     # NOQA


def test_isproperty(app):
    from target.functions import func
    from target.methods import Base

    assert inspect.isproperty(Base.prop) is True        # property of class
    assert inspect.isproperty(Base().prop) is False     # property of instance
    assert inspect.isproperty(Base.meth) is False       # method of class
    assert inspect.isproperty(Base().meth) is False     # method of instance
    assert inspect.isproperty(func) is False            # function


def test_unpartial():
    def func1(a, b, c):
        pass

    func2 = functools.partial(func1, 1)
    func2.__doc__ = "func2"
    func3 = functools.partial(func2, 2)  # nested partial object

    assert inspect.unpartial(func2) is func1
    assert inspect.unpartial(func3) is func1
