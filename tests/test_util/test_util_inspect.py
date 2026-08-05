"""Tests util.inspect functions."""

from __future__ import annotations

import ast
import datetime
import enum
import functools
import types
from inspect import Parameter
from typing import Callable, List, Optional, Union  # NoQA: UP035

import pytest

from sphinx.util import inspect
from sphinx.util.inspect import (
    TypeAliasForwardRef,
    TypeAliasNamespace,
    stringify_signature,
)
from sphinx.util.typing import stringify_annotation


class Base:
    def meth(self):
        pass

    @staticmethod
    def staticmeth():
        pass

    @classmethod
    def classmeth(cls):
        pass

    @property
    def prop(self):
        pass

    partialmeth = functools.partialmethod(meth)

    async def coroutinemeth(self):
        pass

    partial_coroutinemeth = functools.partialmethod(coroutinemeth)

    @classmethod
    async def coroutineclassmeth(cls):
        """A documented coroutine classmethod"""
        pass


class Inherited(Base):
    pass


class MyInt(int):
    @classmethod
    def classmeth(cls):
        pass


class MyIntOverride(MyInt):
    @classmethod
    def from_bytes(cls, *a, **kw):
        return super().from_bytes(*a, **kw)

    def conjugate(self):
        return super().conjugate()


def func():
    pass


async def coroutinefunc():
    pass


async def asyncgenerator():  # NoQA: RUF029
    yield


partial_func = functools.partial(func)
partial_coroutinefunc = functools.partial(coroutinefunc)

builtin_func = print
partial_builtin_func = functools.partial(print)


class Descriptor:
    def __get__(self, obj, typ=None):
        pass


class _Callable:
    def __call__(self):
        pass


def _decorator(f):
    @functools.wraps(f)
    def wrapper():
        return f()

    return wrapper


def forward_reference_in_args(x: Foo) -> None:  # type: ignore[name-defined] # noqa: F821
    pass


def forward_reference_in_return() -> Foo:  # type: ignore[name-defined] # noqa: F821
    pass


def test_TypeAliasForwardRef():
    alias = TypeAliasForwardRef('example')
    sig_str = stringify_annotation(alias, 'fully-qualified-except-typing')
    assert sig_str == "TypeAliasForwardRef('example')"

    alias = Optional[alias]  # NoQA: UP045
    sig_str = stringify_annotation(alias, 'fully-qualified-except-typing')
    assert sig_str == "TypeAliasForwardRef('example') | None"

    alias = alias | None
    sig_str = stringify_annotation(alias, 'fully-qualified-except-typing')
    assert sig_str == "TypeAliasForwardRef('example') | None"

    alias = None | alias  # NoQA: RUF036
    sig_str = stringify_annotation(alias, 'fully-qualified-except-typing')
    assert sig_str == "None | TypeAliasForwardRef('example')"


def test_TypeAliasNamespace() -> None:
    import logging.config

    type_alias = TypeAliasNamespace({
        'logging.Filter': 'MyFilter',
        'logging.Handler': 'MyHandler',
        'logging.handlers.SyslogHandler': 'MySyslogHandler',
    })

    assert type_alias['logging'].Filter == 'MyFilter'
    assert type_alias['logging'].Handler == 'MyHandler'
    assert type_alias['logging'].handlers.SyslogHandler == 'MySyslogHandler'
    assert type_alias['logging'].Logger == logging.Logger
    assert type_alias['logging'].config == logging.config

    with pytest.raises(KeyError):
        assert type_alias['log']

    with pytest.raises(KeyError):
        assert type_alias['unknown']


def test_signature() -> None:
    # literals
    with pytest.raises(TypeError):
        inspect.signature(1)  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        inspect.signature('')  # type: ignore[arg-type]

    # builtins are supported on a case-by-case basis, depending on whether
    # they define __text_signature__
    if getattr(list, '__text_signature__', None):
        sig = inspect.stringify_signature(inspect.signature(list))
        assert sig == '(iterable=(), /)'
    else:
        with pytest.raises(ValueError, match='no signature found for builtin type'):
            inspect.signature(list)
    with pytest.raises(ValueError, match='no signature found for builtin type'):
        inspect.signature(range)

    # normal function
    def func(a, b, c=1, d=2, *e, **f):
        pass

    sig = inspect.stringify_signature(inspect.signature(func))
    assert sig == '(a, b, c=1, d=2, *e, **f)'

    # forward references
    sig = inspect.stringify_signature(inspect.signature(forward_reference_in_args))
    assert sig == '(x: Foo) -> None'

    sig = inspect.stringify_signature(inspect.signature(forward_reference_in_return))
    assert sig == '() -> Foo'


def test_signature_partial() -> None:
    def fun(a, b, c=1, d=2):
        pass

    p = functools.partial(fun, 10, c=11)

    sig = inspect.signature(p)
    assert stringify_signature(sig) == '(b, *, c=11, d=2)'


def test_signature_methods() -> None:
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


def test_signature_partialmethod() -> None:
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


def test_signature_annotations() -> None:
    import tests.test_util.typing_test_data as mod

    # Class annotations
    sig = inspect.signature(mod.f0)
    assert stringify_signature(sig) == '(x: int, y: numbers.Integral) -> None'

    # Generic types with concrete parameters
    sig = inspect.signature(mod.f1)
    assert stringify_signature(sig) == '(x: list[int]) -> typing.List[int]'

    # TypeVars and generic types with TypeVars
    sig = inspect.signature(mod.f2)
    assert stringify_signature(sig) == (
        '(x: typing.List[tests.test_util.typing_test_data.T],'
        ' y: typing.List[tests.test_util.typing_test_data.T_co],'
        ' z: tests.test_util.typing_test_data.T'
        ') -> typing.List[tests.test_util.typing_test_data.T_contra]'
    )

    # Union types
    sig = inspect.signature(mod.f3)
    assert stringify_signature(sig) == '(x: str | numbers.Integral) -> None'

    # Quoted annotations
    sig = inspect.signature(mod.f4)
    assert stringify_signature(sig) == '(x: str, y: str) -> None'

    # Keyword-only arguments
    sig = inspect.signature(mod.f5)
    assert stringify_signature(sig) == '(x: int, *, y: str, z: str) -> None'

    # Keyword-only arguments with varargs
    sig = inspect.signature(mod.f6)
    assert stringify_signature(sig) == '(x: int, *args, y: str, z: str) -> None'

    # Space around '=' for defaults
    sig = inspect.signature(mod.f7)
    sig_str = stringify_signature(sig)
    assert sig_str == '(x: int = None, y: dict = {}) -> None'

    # Callable types
    sig = inspect.signature(mod.f8)
    assert stringify_signature(sig) == '(x: typing.Callable[[int, str], int]) -> None'

    sig = inspect.signature(mod.f9)
    assert stringify_signature(sig) == '(x: typing.Callable) -> None'

    # Tuple types
    sig = inspect.signature(mod.f10)
    sig_str = stringify_signature(sig)
    assert sig_str == '(x: typing.Tuple[int, str], y: typing.Tuple[int, ...]) -> None'

    # Instance annotations
    sig = inspect.signature(mod.f11)
    assert stringify_signature(sig) == '(x: CustomAnnotation, y: 123) -> None'

    # tuple with more than two items
    sig = inspect.signature(mod.f12)
    assert stringify_signature(sig) == '() -> typing.Tuple[int, str, int]'

    # optional
    sig = inspect.signature(mod.f13)
    assert stringify_signature(sig) == '() -> str | None'

    # optional union
    sig = inspect.signature(mod.f20)
    assert stringify_signature(sig) in {
        '() -> int | str | None',
        '() -> str | int | None',
    }

    # Any
    sig = inspect.signature(mod.f14)
    assert stringify_signature(sig) == '() -> typing.Any'

    # ForwardRef
    sig = inspect.signature(mod.f15)
    assert stringify_signature(sig) == '(x: Unknown, y: int) -> typing.Any'

    # keyword only arguments (1)
    sig = inspect.signature(mod.f16)
    assert stringify_signature(sig) == '(arg1, arg2, *, arg3=None, arg4=None)'

    # keyword only arguments (2)
    sig = inspect.signature(mod.f17)
    assert stringify_signature(sig) == '(*, arg3, arg4)'

    sig = inspect.signature(mod.f18)
    assert stringify_signature(sig) == (
        '(self, arg1: int | typing.Tuple = 10) -> typing.List[typing.Dict]'
    )

    # annotations for variadic and keyword parameters
    sig = inspect.signature(mod.f19)
    assert stringify_signature(sig) == '(*args: int, **kwargs: str)'

    # default value is inspect.Signature.empty
    sig = inspect.signature(mod.f21)
    assert stringify_signature(sig) == "(arg1='whatever', arg2)"

    # type hints by string
    sig = inspect.signature(mod.Node.children)
    sig_str = stringify_signature(sig)
    assert sig_str == '(self) -> typing.List[tests.test_util.typing_test_data.Node]'

    sig = inspect.signature(mod.Node.__init__)
    sig_str = stringify_signature(sig)
    assert sig_str == (
        '(self, parent: tests.test_util.typing_test_data.Node | None) -> None'
    )

    # show_annotation is False
    sig = inspect.signature(mod.f7)
    assert stringify_signature(sig, show_annotation=False) == '(x=None, y={})'

    # show_return_annotation is False
    sig = inspect.signature(mod.f7)
    sig_str = stringify_signature(sig, show_return_annotation=False)
    assert sig_str == '(x: int = None, y: dict = {})'

    # unqualified_typehints is True
    sig = inspect.signature(mod.f7)
    sig_str = stringify_signature(sig, unqualified_typehints=True)
    assert sig_str == '(x: int = None, y: dict = {}) -> None'

    # case: separator at head
    sig = inspect.signature(mod.f22)
    assert stringify_signature(sig) == '(*, a, b)'

    # case: separator in the middle
    sig = inspect.signature(mod.f23)
    assert stringify_signature(sig) == '(a, b, /, c, d)'

    sig = inspect.signature(mod.f24)
    assert stringify_signature(sig) == '(a, /, *, b)'

    # case: separator at tail
    sig = inspect.signature(mod.f25)
    assert stringify_signature(sig) == '(a, b, /)'

    # collapse Literal types
    sig = inspect.signature(mod.f26)
    sig_str = stringify_signature(sig)
    assert sig_str == (
        "(x: typing.Literal[1, 2, 3] = 1, y: typing.Literal['a', 'b'] = 'a') -> None"
    )


def test_signature_from_str_basic() -> None:
    signature = '(a, b, *args, c=0, d="blah", **kwargs)'
    sig = inspect.signature_from_str(signature)
    assert list(sig.parameters.keys()) == ['a', 'b', 'args', 'c', 'd', 'kwargs']
    assert sig.parameters['a'].name == 'a'
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['a'].annotation == Parameter.empty
    assert sig.parameters['b'].name == 'b'
    assert sig.parameters['b'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['b'].default == Parameter.empty
    assert sig.parameters['b'].annotation == Parameter.empty
    assert sig.parameters['args'].name == 'args'
    assert sig.parameters['args'].kind == Parameter.VAR_POSITIONAL
    assert sig.parameters['args'].default == Parameter.empty
    assert sig.parameters['args'].annotation == Parameter.empty
    assert sig.parameters['c'].name == 'c'
    assert sig.parameters['c'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['c'].default == '0'
    assert sig.parameters['c'].annotation == Parameter.empty
    assert sig.parameters['d'].name == 'd'
    assert sig.parameters['d'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['d'].default == "'blah'"
    assert sig.parameters['d'].annotation == Parameter.empty
    assert sig.parameters['kwargs'].name == 'kwargs'
    assert sig.parameters['kwargs'].kind == Parameter.VAR_KEYWORD
    assert sig.parameters['kwargs'].default == Parameter.empty
    assert sig.parameters['kwargs'].annotation == Parameter.empty
    assert sig.return_annotation == Parameter.empty


def test_signature_from_str_default_values() -> None:
    signature = (
        '(a=0, b=0.0, c="str", d=b"bytes", e=..., f=True, '
        'g=[1, 2, 3], h={"a": 1}, i={1, 2, 3}, '
        'j=lambda x, y: None, k=None, l=object(), m=foo.bar.CONSTANT)'
    )
    sig = inspect.signature_from_str(signature)
    assert sig.parameters['a'].default == '0'
    assert sig.parameters['b'].default == '0.0'
    assert sig.parameters['c'].default == "'str'"
    assert sig.parameters['d'].default == "b'bytes'"
    assert sig.parameters['e'].default == '...'
    assert sig.parameters['f'].default == 'True'
    assert sig.parameters['g'].default == '[1, 2, 3]'
    assert sig.parameters['h'].default == "{'a': 1}"
    assert sig.parameters['i'].default == '{1, 2, 3}'
    assert sig.parameters['j'].default == 'lambda x, y: ...'
    assert sig.parameters['k'].default == 'None'
    assert sig.parameters['l'].default == 'object()'
    assert sig.parameters['m'].default == 'foo.bar.CONSTANT'


def test_signature_from_str_annotations() -> None:
    signature = '(a: int, *args: bytes, b: str = "blah", **kwargs: float) -> None'
    sig = inspect.signature_from_str(signature)
    assert list(sig.parameters.keys()) == ['a', 'args', 'b', 'kwargs']
    assert sig.parameters['a'].annotation == 'int'
    assert sig.parameters['args'].annotation == 'bytes'
    assert sig.parameters['b'].annotation == 'str'
    assert sig.parameters['kwargs'].annotation == 'float'
    assert sig.return_annotation == 'None'


def test_signature_from_str_complex_annotations() -> None:
    sig = inspect.signature_from_str('() -> Tuple[str, int, ...]')
    assert sig.return_annotation == 'Tuple[str, int, ...]'

    sig = inspect.signature_from_str('() -> Callable[[int, int], int]')
    assert sig.return_annotation == 'Callable[[int, int], int]'


def test_signature_from_str_kwonly_args() -> None:
    sig = inspect.signature_from_str('(a, *, b)')
    assert list(sig.parameters.keys()) == ['a', 'b']
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['b'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['b'].default == Parameter.empty


def test_signature_from_str_positionaly_only_args() -> None:
    sig = inspect.signature_from_str('(a, b=0, /, c=1)')
    assert list(sig.parameters.keys()) == ['a', 'b', 'c']
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['b'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['b'].default == '0'
    assert sig.parameters['c'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['c'].default == '1'


def test_signature_from_str_invalid() -> None:
    with pytest.raises(SyntaxError):
        inspect.signature_from_str('')


def test_signature_from_ast():
    signature = 'def func(a, b, *args, c=0, d="blah", **kwargs): pass'
    tree = ast.parse(signature)
    sig = inspect.signature_from_ast(tree.body[0])
    assert list(sig.parameters.keys()) == ['a', 'b', 'args', 'c', 'd', 'kwargs']
    assert sig.parameters['a'].name == 'a'
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['a'].annotation == Parameter.empty
    assert sig.parameters['b'].name == 'b'
    assert sig.parameters['b'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['b'].default == Parameter.empty
    assert sig.parameters['b'].annotation == Parameter.empty
    assert sig.parameters['args'].name == 'args'
    assert sig.parameters['args'].kind == Parameter.VAR_POSITIONAL
    assert sig.parameters['args'].default == Parameter.empty
    assert sig.parameters['args'].annotation == Parameter.empty
    assert sig.parameters['c'].name == 'c'
    assert sig.parameters['c'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['c'].default == '0'
    assert sig.parameters['c'].annotation == Parameter.empty
    assert sig.parameters['d'].name == 'd'
    assert sig.parameters['d'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['d'].default == "'blah'"
    assert sig.parameters['d'].annotation == Parameter.empty
    assert sig.parameters['kwargs'].name == 'kwargs'
    assert sig.parameters['kwargs'].kind == Parameter.VAR_KEYWORD
    assert sig.parameters['kwargs'].default == Parameter.empty
    assert sig.parameters['kwargs'].annotation == Parameter.empty
    assert sig.return_annotation == Parameter.empty


def test_safe_getattr_with_default() -> None:
    class Foo:
        def __getattr__(self, item):
            raise Exception

    obj = Foo()

    result = inspect.safe_getattr(obj, 'bar', 'baz')

    assert result == 'baz'


def test_safe_getattr_with_exception() -> None:
    class Foo:
        def __getattr__(self, item):
            raise Exception

    obj = Foo()

    with pytest.raises(AttributeError, match='bar'):
        inspect.safe_getattr(obj, 'bar')


def test_safe_getattr_with_property_exception() -> None:
    class Foo:
        @property
        def bar(self):
            raise Exception

    obj = Foo()

    with pytest.raises(AttributeError, match='bar'):
        inspect.safe_getattr(obj, 'bar')


def test_safe_getattr_with___dict___override() -> None:
    class Foo:
        @property
        def __dict__(self):
            raise Exception

    obj = Foo()

    with pytest.raises(AttributeError, match='bar'):
        inspect.safe_getattr(obj, 'bar')


def test_dictionary_sorting() -> None:
    dictionary = {'c': 3, 'a': 1, 'd': 2, 'b': 4}
    description = inspect.object_description(dictionary)
    assert description == "{'a': 1, 'b': 4, 'c': 3, 'd': 2}"


def test_set_sorting() -> None:
    set_ = set('gfedcba')
    description = inspect.object_description(set_)
    assert description == "{'a', 'b', 'c', 'd', 'e', 'f', 'g'}"


def test_set_sorting_enum() -> None:
    class MyEnum(enum.Enum):
        a = 1
        b = 2
        c = 3

    set_ = set(MyEnum)
    description = inspect.object_description(set_)
    assert description == '{MyEnum.a, MyEnum.b, MyEnum.c}'


def test_set_sorting_fallback() -> None:
    set_ = {None, 1}
    description = inspect.object_description(set_)
    assert description == '{1, None}'


def test_deterministic_nested_collection_descriptions() -> None:
    # sortable
    assert inspect.object_description([{1, 2, 3, 10}]) == '[{1, 2, 3, 10}]'
    assert inspect.object_description(({1, 2, 3, 10},)) == '({1, 2, 3, 10},)'
    # non-sortable (elements of varying datatype)
    assert inspect.object_description([{None, 1}]) == '[{1, None}]'
    assert inspect.object_description(({None, 1},)) == '({1, None},)'
    assert inspect.object_description([{None, 1, 'A'}]) == "[{'A', 1, None}]"
    assert inspect.object_description(({None, 1, 'A'},)) == "({'A', 1, None},)"


def test_frozenset_sorting() -> None:
    frozenset_ = frozenset('gfedcba')
    description = inspect.object_description(frozenset_)
    assert description == "frozenset({'a', 'b', 'c', 'd', 'e', 'f', 'g'})"


def test_frozenset_sorting_fallback() -> None:
    frozenset_ = frozenset((None, 1))
    description = inspect.object_description(frozenset_)
    assert description == 'frozenset({1, None})'


def test_nested_tuple_sorting():
    tuple_ = ({'c', 'b', 'a'},)  # nb. trailing comma
    description = inspect.object_description(tuple_)
    assert description == "({'a', 'b', 'c'},)"

    tuple_ = ({'c', 'b', 'a'}, {'f', 'e', 'd'})
    description = inspect.object_description(tuple_)
    assert description == "({'a', 'b', 'c'}, {'d', 'e', 'f'})"


def test_recursive_collection_description():
    dict_a_, dict_b_ = {'a': 1}, {'b': 2}
    dict_a_['link'], dict_b_['link'] = dict_b_, dict_a_
    description_a, description_b = (
        inspect.object_description(dict_a_),
        inspect.object_description(dict_b_),
    )
    assert description_a == "{'a': 1, 'link': {'b': 2, 'link': dict(...)}}"
    assert description_b == "{'b': 2, 'link': {'a': 1, 'link': dict(...)}}"

    list_c_, list_d_ = [1, 2, 3, 4], [5, 6, 7, 8]
    list_c_.append(list_d_)
    list_d_.append(list_c_)
    description_c, description_d = (
        inspect.object_description(list_c_),
        inspect.object_description(list_d_),
    )

    assert description_c == '[1, 2, 3, 4, [5, 6, 7, 8, list(...)]]'
    assert description_d == '[5, 6, 7, 8, [1, 2, 3, 4, list(...)]]'


def test_dict_customtype() -> None:
    class CustomType:
        def __init__(self, value):
            self._value = value

        def __repr__(self):
            return '<CustomType(%r)>' % self._value

    dictionary = {CustomType(2): 2, CustomType(1): 1}
    description = inspect.object_description(dictionary)
    # Type is unsortable, just check that it does not crash
    assert '<CustomType(2)>: 2' in description


def test_object_description_enum() -> None:
    class MyEnum(enum.Enum):
        FOO = 1
        BAR = 2

    assert inspect.object_description(MyEnum.FOO) == 'MyEnum.FOO'


def test_object_description_enum_custom_repr() -> None:
    class MyEnum(enum.Enum):
        FOO = 1
        BAR = 2

        def __repr__(self):
            return self.name

    assert inspect.object_description(MyEnum.FOO) == 'FOO'


def test_getslots() -> None:
    class Foo:
        pass

    class Bar:
        __slots__ = ['attr']

    class Baz:
        __slots__ = {'attr': 'docstring'}

    class Qux:
        __slots__ = 'attr'  # NoQA: PLC0205

    assert inspect.getslots(Foo) is None
    assert inspect.getslots(Bar) == {'attr': None}
    assert inspect.getslots(Baz) == {'attr': 'docstring'}
    assert inspect.getslots(Qux) == {'attr': None}

    with pytest.raises(TypeError):
        inspect.getslots(Bar())


@pytest.mark.parametrize(
    ('expect', 'klass', 'name'),
    [
        # class methods
        (True, Base, 'classmeth'),
        (True, Inherited, 'classmeth'),
        (True, MyInt, 'classmeth'),
        (True, MyIntOverride, 'from_bytes'),
        # non class methods
        (False, Base, 'meth'),
        (False, Inherited, 'meth'),
        (False, MyInt, 'conjugate'),
        (False, MyIntOverride, 'conjugate'),
    ],
)
def test_isclassmethod(expect, klass, name):
    subject = getattr(klass, name)
    assert inspect.isclassmethod(subject) is expect
    assert inspect.isclassmethod(None, klass, name) is expect


@pytest.mark.parametrize(
    ('expect', 'klass', 'dict_key'),
    [
        # int.from_bytes is not a class method descriptor
        # but int.__dict__['from_bytes'] is one.
        (True, int, 'from_bytes'),
        (True, MyInt, 'from_bytes'),  # inherited
        # non class method descriptors
        (False, Base, 'classmeth'),
        (False, Inherited, 'classmeth'),
        (False, int, '__init__'),
        (False, int, 'conjugate'),
        (False, MyInt, 'classmeth'),
        (False, MyIntOverride, 'from_bytes'),  # overridden in pure Python
    ],
)
def test_is_classmethod_descriptor(expect, klass, dict_key):
    in_dict = dict_key in klass.__dict__
    subject = klass.__dict__.get(dict_key)
    assert inspect.is_classmethod_descriptor(subject) is (in_dict and expect)
    assert inspect.is_classmethod_descriptor(None, klass, dict_key) is expect

    method = getattr(klass, dict_key)
    assert not inspect.is_classmethod_descriptor(method)


@pytest.mark.parametrize(
    ('expect', 'klass', 'dict_key'),
    [
        # class method descriptors
        (True, int, 'from_bytes'),
        (True, bytes, 'fromhex'),
        (True, MyInt, 'from_bytes'),  # in C only
        # non class method descriptors
        (False, Base, 'classmeth'),
        (False, Inherited, 'classmeth'),
        (False, int, '__init__'),
        (False, int, 'conjugate'),
        (False, MyInt, 'classmeth'),
        (False, MyIntOverride, 'from_bytes'),  # overridden in pure Python
    ],
)
def test_is_builtin_classmethod_like(expect, klass, dict_key):
    method = getattr(klass, dict_key)
    assert inspect.is_builtin_classmethod_like(method) is expect
    assert inspect.is_builtin_classmethod_like(None, klass, dict_key) is expect


@pytest.mark.parametrize(
    ('expect', 'klass', 'name'),
    [
        # regular class methods
        (True, Base, 'classmeth'),
        (True, Inherited, 'classmeth'),
        (True, MyInt, 'classmeth'),
        # inherited C class method
        (True, MyIntOverride, 'from_bytes'),
        # class method descriptors
        (True, int, 'from_bytes'),
        (True, bytes, 'fromhex'),
        (True, MyInt, 'from_bytes'),  # in C only
        # not classmethod-like
        (False, int, '__init__'),
        (False, int, 'conjugate'),
        (False, MyIntOverride, 'conjugate'),  # overridden in pure Python
    ],
)
def test_is_classmethod_like(expect, klass, name):
    subject = getattr(klass, name)
    assert inspect.is_classmethod_like(subject) is expect


def test_isstaticmethod() -> None:
    assert inspect.isstaticmethod(Base.staticmeth, Base, 'staticmeth')
    assert not inspect.isstaticmethod(Base.meth, Base, 'meth')
    assert inspect.isstaticmethod(Inherited.staticmeth, Inherited, 'staticmeth')
    assert not inspect.isstaticmethod(Inherited.meth, Inherited, 'meth')


def test_iscoroutinefunction() -> None:
    # function
    assert not inspect.iscoroutinefunction(func)
    # coroutine
    assert inspect.iscoroutinefunction(coroutinefunc)
    # partial-ed coroutine
    assert inspect.iscoroutinefunction(partial_coroutinefunc)
    # method
    assert not inspect.iscoroutinefunction(Base.meth)
    # coroutine-method
    assert inspect.iscoroutinefunction(Base.coroutinemeth)
    # coroutine classmethod
    assert inspect.iscoroutinefunction(Base.__dict__['coroutineclassmeth'])

    # partial-ed coroutine-method
    partial_coroutinemeth = Base.__dict__['partial_coroutinemeth']
    assert inspect.iscoroutinefunction(partial_coroutinemeth)


def test_iscoroutinefunction_wrapped() -> None:
    # function wrapping a callable obj
    assert inspect.isfunction(_decorator(coroutinefunc))


def test_isfunction() -> None:
    # fmt: off
    assert inspect.isfunction(func)                      # function
    assert inspect.isfunction(partial_func)              # partial-ed function
    assert inspect.isfunction(Base.meth)                 # method of class
    assert inspect.isfunction(Base.partialmeth)          # partial-ed method of class
    assert not inspect.isfunction(Base().meth)           # method of instance
    assert not inspect.isfunction(builtin_func)          # builtin function
    assert not inspect.isfunction(partial_builtin_func)  # partial-ed builtin function
    # fmt: on


def test_isfunction_wrapped() -> None:
    # function wrapping a callable obj
    assert inspect.isfunction(_decorator(_Callable()))


def test_isbuiltin() -> None:
    # fmt: off
    assert inspect.isbuiltin(builtin_func)          # builtin function
    assert inspect.isbuiltin(partial_builtin_func)  # partial-ed builtin function
    assert not inspect.isbuiltin(func)              # function
    assert not inspect.isbuiltin(partial_func)      # partial-ed function
    assert not inspect.isbuiltin(Base.meth)         # method of class
    assert not inspect.isbuiltin(Base().meth)       # method of instance
    # fmt: on


def test_isdescriptor() -> None:
    # fmt: off
    assert inspect.isdescriptor(Base.prop)        # property of class
    assert not inspect.isdescriptor(Base().prop)  # property of instance
    assert inspect.isdescriptor(Base.meth)        # method of class
    assert inspect.isdescriptor(Base().meth)      # method of instance
    assert inspect.isdescriptor(func)             # function
    # fmt: on


def test_isattributedescriptor() -> None:
    # fmt: off
    assert inspect.isattributedescriptor(Base.prop)                      # property
    assert not inspect.isattributedescriptor(Base.meth)                  # method
    assert not inspect.isattributedescriptor(Base.staticmeth)            # staticmethod
    assert not inspect.isattributedescriptor(Base.classmeth)             # classmetho
    assert not inspect.isattributedescriptor(Descriptor)                 # custom descriptor class
    assert not inspect.isattributedescriptor(str.join)                   # MethodDescriptorType
    assert not inspect.isattributedescriptor(object.__init__)            # WrapperDescriptorType
    assert not inspect.isattributedescriptor(dict.__dict__['fromkeys'])  # ClassMethodDescriptorType
    assert inspect.isattributedescriptor(types.FrameType.f_locals)       # GetSetDescriptorType
    assert inspect.isattributedescriptor(datetime.timedelta.days)        # MemberDescriptorType
    # fmt: on

    try:
        # _testcapi module cannot be importable in some distro
        # See: https://github.com/sphinx-doc/sphinx/issues/9868
        import _testcapi  # type: ignore[import-not-found]

        # instancemethod (C-API)
        testinstancemethod = _testcapi.instancemethod(str.__repr__)
        assert not inspect.isattributedescriptor(testinstancemethod)
    except ImportError:
        pass


def test_isproperty() -> None:
    # fmt: off
    assert inspect.isproperty(Base.prop)        # property of class
    assert not inspect.isproperty(Base().prop)  # property of instance
    assert not inspect.isproperty(Base.meth)    # method of class
    assert not inspect.isproperty(Base().meth)  # method of instance
    assert not inspect.isproperty(func)         # function
    # fmt: on


def test_isgenericalias() -> None:
    #: A list of int
    T = List[int]  # NoQA: UP006
    S = list[Union[str, None]]  # NoQA: UP007

    C = Callable[[int], None]  # a generic alias not having a doccomment

    assert inspect.isgenericalias(C)
    assert inspect.isgenericalias(Callable)
    assert inspect.isgenericalias(T)
    assert inspect.isgenericalias(List)  # NoQA: UP006
    assert inspect.isgenericalias(S)
    assert not inspect.isgenericalias(list)
    assert not inspect.isgenericalias([])
    assert not inspect.isgenericalias(object())
    assert not inspect.isgenericalias(Base)


def test_unpartial() -> None:
    def func1(a, b, c):
        pass

    func2 = functools.partial(func1, 1)
    func2.__doc__ = 'func2'
    func3 = functools.partial(func2, 2)  # nested partial object

    assert inspect.unpartial(func2) is func1
    assert inspect.unpartial(func3) is func1


def test_getdoc_inherited_classmethod():
    class Foo:
        @classmethod
        def meth(cls):
            """Docstring
            indented text
            """

    class Bar(Foo):
        @classmethod
        def meth(cls):
            # inherited classmethod
            pass

    assert inspect.getdoc(Bar.meth, getattr, False, Bar, 'meth') is None
    assert inspect.getdoc(Bar.meth, getattr, True, Bar, 'meth') == Foo.meth.__doc__


def test_getdoc_inherited_decorated_method():
    class Foo:
        def meth(self):
            """Docstring
            indented text
            """

    class Bar(Foo):
        @functools.lru_cache  # NoQA: B019
        def meth(self):
            # inherited and decorated method
            pass

    assert inspect.getdoc(Bar.meth, getattr, False, Bar, 'meth') is None
    assert inspect.getdoc(Bar.meth, getattr, True, Bar, 'meth') == Foo.meth.__doc__


def test_is_builtin_class_method() -> None:
    class MyInt(int):
        def my_method(self) -> None:
            pass

    assert inspect.is_builtin_class_method(MyInt, 'to_bytes')
    assert inspect.is_builtin_class_method(MyInt, '__init__')
    assert not inspect.is_builtin_class_method(MyInt, 'my_method')
    assert not inspect.is_builtin_class_method(MyInt, 'does_not_exist')
    assert not inspect.is_builtin_class_method(4, 'still does not crash')

    class ObjectWithMroAttr:
        def __init__(self, mro_attr):
            self.__mro__ = mro_attr

    assert not inspect.is_builtin_class_method(
        ObjectWithMroAttr([1, 2, 3]), 'still does not crash'
    )
