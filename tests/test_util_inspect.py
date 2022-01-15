"""
    test_util_inspect
    ~~~~~~~~~~~~~~~

    Tests util.inspect functions.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import ast
import datetime
import enum
import functools
import sys
import types
from inspect import Parameter

import pytest

from sphinx.util import inspect
from sphinx.util.inspect import TypeAliasNamespace, stringify_signature


def test_TypeAliasNamespace():
    import logging.config
    type_alias = TypeAliasNamespace({'logging.Filter': 'MyFilter',
                                     'logging.Handler': 'MyHandler',
                                     'logging.handlers.SyslogHandler': 'MySyslogHandler'})

    assert type_alias['logging'].Filter == 'MyFilter'
    assert type_alias['logging'].Handler == 'MyHandler'
    assert type_alias['logging'].handlers.SyslogHandler == 'MySyslogHandler'
    assert type_alias['logging'].Logger == logging.Logger
    assert type_alias['logging'].config == logging.config

    with pytest.raises(KeyError):
        assert type_alias['log']

    with pytest.raises(KeyError):
        assert type_alias['unknown']


def test_signature():
    # literals
    with pytest.raises(TypeError):
        inspect.signature(1)

    with pytest.raises(TypeError):
        inspect.signature('')

    # builtins are supported on a case-by-case basis, depending on whether
    # they define __text_signature__
    if getattr(list, '__text_signature__', None):
        sig = inspect.stringify_signature(inspect.signature(list))
        assert sig == '(iterable=(), /)'
    else:
        with pytest.raises(ValueError):
            inspect.signature(list)

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
    from .typing_test_data import (Node, f0, f1, f2, f3, f4, f5, f6, f7, f8, f9, f10, f11, f12,
                                   f13, f14, f15, f16, f17, f18, f19, f20, f21)

    # Class annotations
    sig = inspect.signature(f0)
    assert stringify_signature(sig) == '(x: int, y: numbers.Integral) -> None'

    # Generic types with concrete parameters
    sig = inspect.signature(f1)
    assert stringify_signature(sig) == '(x: typing.List[int]) -> typing.List[int]'

    # TypeVars and generic types with TypeVars
    sig = inspect.signature(f2)
    if sys.version_info < (3, 7):
        assert stringify_signature(sig) == ('(x: typing.List[typing.T],'
                                            ' y: typing.List[typing.T_co],'
                                            ' z: typing.T'
                                            ') -> typing.List[typing.T_contra]')
    else:
        assert stringify_signature(sig) == ('(x: typing.List[tests.typing_test_data.T],'
                                            ' y: typing.List[tests.typing_test_data.T_co],'
                                            ' z: tests.typing_test_data.T'
                                            ') -> typing.List[tests.typing_test_data.T_contra]')

    # Union types
    sig = inspect.signature(f3)
    assert stringify_signature(sig) == '(x: typing.Union[str, numbers.Integral]) -> None'

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
    assert stringify_signature(sig) == '(x: typing.Optional[int] = None, y: dict = {}) -> None'

    # Callable types
    sig = inspect.signature(f8)
    assert stringify_signature(sig) == '(x: typing.Callable[[int, str], int]) -> None'

    sig = inspect.signature(f9)
    assert stringify_signature(sig) == '(x: typing.Callable) -> None'

    # Tuple types
    sig = inspect.signature(f10)
    assert stringify_signature(sig) == '(x: typing.Tuple[int, str], y: typing.Tuple[int, ...]) -> None'

    # Instance annotations
    sig = inspect.signature(f11)
    assert stringify_signature(sig) == '(x: CustomAnnotation, y: 123) -> None'

    # tuple with more than two items
    sig = inspect.signature(f12)
    assert stringify_signature(sig) == '() -> typing.Tuple[int, str, int]'

    # optional
    sig = inspect.signature(f13)
    assert stringify_signature(sig) == '() -> typing.Optional[str]'

    # optional union
    sig = inspect.signature(f20)
    assert stringify_signature(sig) in ('() -> typing.Optional[typing.Union[int, str]]',
                                        '() -> typing.Optional[typing.Union[str, int]]')

    # Any
    sig = inspect.signature(f14)
    assert stringify_signature(sig) == '() -> typing.Any'

    # ForwardRef
    sig = inspect.signature(f15)
    assert stringify_signature(sig) == '(x: Unknown, y: int) -> typing.Any'

    # keyword only arguments (1)
    sig = inspect.signature(f16)
    assert stringify_signature(sig) == '(arg1, arg2, *, arg3=None, arg4=None)'

    # keyword only arguments (2)
    sig = inspect.signature(f17)
    assert stringify_signature(sig) == '(*, arg3, arg4)'

    sig = inspect.signature(f18)
    assert stringify_signature(sig) == ('(self, arg1: typing.Union[int, typing.Tuple] = 10) -> '
                                        'typing.List[typing.Dict]')

    # annotations for variadic and keyword parameters
    sig = inspect.signature(f19)
    assert stringify_signature(sig) == '(*args: int, **kwargs: str)'

    # default value is inspect.Signature.empty
    sig = inspect.signature(f21)
    assert stringify_signature(sig) == "(arg1='whatever', arg2)"

    # type hints by string
    sig = inspect.signature(Node.children)
    assert stringify_signature(sig) == '(self) -> typing.List[tests.typing_test_data.Node]'

    sig = inspect.signature(Node.__init__)
    assert stringify_signature(sig) == '(self, parent: typing.Optional[tests.typing_test_data.Node]) -> None'

    # show_annotation is False
    sig = inspect.signature(f7)
    assert stringify_signature(sig, show_annotation=False) == '(x=None, y={})'

    # show_return_annotation is False
    sig = inspect.signature(f7)
    assert stringify_signature(sig, show_return_annotation=False) == '(x: typing.Optional[int] = None, y: dict = {})'

    # unqualified_typehints is True
    sig = inspect.signature(f7)
    assert stringify_signature(sig, unqualified_typehints=True) == '(x: ~typing.Optional[int] = None, y: dict = {}) -> None'


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
@pytest.mark.sphinx(testroot='ext-autodoc')
def test_signature_annotations_py38(app):
    from target.pep570 import bar, baz, foo, qux

    # case: separator at head
    sig = inspect.signature(foo)
    assert stringify_signature(sig) == '(*, a, b)'

    # case: separator in the middle
    sig = inspect.signature(bar)
    assert stringify_signature(sig) == '(a, b, /, c, d)'

    sig = inspect.signature(baz)
    assert stringify_signature(sig) == '(a, /, *, b)'

    # case: separator at tail
    sig = inspect.signature(qux)
    assert stringify_signature(sig) == '(a, b, /)'


def test_signature_from_str_basic():
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


def test_signature_from_str_default_values():
    signature = ('(a=0, b=0.0, c="str", d=b"bytes", e=..., f=True, '
                 'g=[1, 2, 3], h={"a": 1}, i={1, 2, 3}, '
                 'j=lambda x, y: None, k=None, l=object(), m=foo.bar.CONSTANT)')
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


def test_signature_from_str_annotations():
    signature = '(a: int, *args: bytes, b: str = "blah", **kwargs: float) -> None'
    sig = inspect.signature_from_str(signature)
    assert list(sig.parameters.keys()) == ['a', 'args', 'b', 'kwargs']
    assert sig.parameters['a'].annotation == "int"
    assert sig.parameters['args'].annotation == "bytes"
    assert sig.parameters['b'].annotation == "str"
    assert sig.parameters['kwargs'].annotation == "float"
    assert sig.return_annotation == 'None'


def test_signature_from_str_complex_annotations():
    sig = inspect.signature_from_str('() -> Tuple[str, int, ...]')
    assert sig.return_annotation == 'Tuple[str, int, ...]'

    sig = inspect.signature_from_str('() -> Callable[[int, int], int]')
    assert sig.return_annotation == 'Callable[[int, int], int]'


def test_signature_from_str_kwonly_args():
    sig = inspect.signature_from_str('(a, *, b)')
    assert list(sig.parameters.keys()) == ['a', 'b']
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['b'].kind == Parameter.KEYWORD_ONLY
    assert sig.parameters['b'].default == Parameter.empty


@pytest.mark.skipif(sys.version_info < (3, 8),
                    reason='python-3.8 or above is required')
def test_signature_from_str_positionaly_only_args():
    sig = inspect.signature_from_str('(a, b=0, /, c=1)')
    assert list(sig.parameters.keys()) == ['a', 'b', 'c']
    assert sig.parameters['a'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['a'].default == Parameter.empty
    assert sig.parameters['b'].kind == Parameter.POSITIONAL_ONLY
    assert sig.parameters['b'].default == '0'
    assert sig.parameters['c'].kind == Parameter.POSITIONAL_OR_KEYWORD
    assert sig.parameters['c'].default == '1'


def test_signature_from_str_invalid():
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


def test_object_description_enum():
    class MyEnum(enum.Enum):
        FOO = 1
        BAR = 2

    assert inspect.object_description(MyEnum.FOO) == "MyEnum.FOO"


def test_getslots():
    class Foo:
        pass

    class Bar:
        __slots__ = ['attr']

    class Baz:
        __slots__ = {'attr': 'docstring'}

    class Qux:
        __slots__ = 'attr'

    assert inspect.getslots(Foo) is None
    assert inspect.getslots(Bar) == {'attr': None}
    assert inspect.getslots(Baz) == {'attr': 'docstring'}
    assert inspect.getslots(Qux) == {'attr': None}

    with pytest.raises(TypeError):
        inspect.getslots(Bar())


@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isclassmethod(app):
    from target.methods import Base, Inherited

    assert inspect.isclassmethod(Base.classmeth) is True
    assert inspect.isclassmethod(Base.meth) is False
    assert inspect.isclassmethod(Inherited.classmeth) is True
    assert inspect.isclassmethod(Inherited.meth) is False


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
    from target.functions import builtin_func, func, partial_builtin_func, partial_func
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
    from target.functions import builtin_func, func, partial_builtin_func, partial_func
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

    try:
        # _testcapi module cannot be importable in some distro
        # refs: https://github.com/sphinx-doc/sphinx/issues/9868
        import _testcapi

        testinstancemethod = _testcapi.instancemethod(str.__repr__)
        assert inspect.isattributedescriptor(testinstancemethod) is False      # instancemethod (C-API)     # NOQA
    except ImportError:
        pass


def test_isproperty(app):
    from target.functions import func
    from target.methods import Base

    assert inspect.isproperty(Base.prop) is True        # property of class
    assert inspect.isproperty(Base().prop) is False     # property of instance
    assert inspect.isproperty(Base.meth) is False       # method of class
    assert inspect.isproperty(Base().meth) is False     # method of instance
    assert inspect.isproperty(func) is False            # function


@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required.')
@pytest.mark.sphinx(testroot='ext-autodoc')
def test_isgenericalias(app):
    from target.genericalias import C, T
    from target.methods import Base

    assert inspect.isgenericalias(C) is True
    assert inspect.isgenericalias(T) is True
    assert inspect.isgenericalias(object()) is False
    assert inspect.isgenericalias(Base) is False


def test_unpartial():
    def func1(a, b, c):
        pass

    func2 = functools.partial(func1, 1)
    func2.__doc__ = "func2"
    func3 = functools.partial(func2, 2)  # nested partial object

    assert inspect.unpartial(func2) is func1
    assert inspect.unpartial(func3) is func1


def test_getdoc_inherited_classmethod():
    class Foo:
        @classmethod
        def meth(self):
            """
            docstring
                indented text
            """

    class Bar(Foo):
        @classmethod
        def meth(self):
            # inherited classmethod
            pass

    assert inspect.getdoc(Bar.meth, getattr, False, Bar, "meth") is None
    assert inspect.getdoc(Bar.meth, getattr, True, Bar, "meth") == Foo.meth.__doc__


def test_getdoc_inherited_decorated_method():
    class Foo:
        def meth(self):
            """
            docstring
                indented text
            """

    class Bar(Foo):
        @functools.lru_cache()
        def meth(self):
            # inherited and decorated method
            pass

    assert inspect.getdoc(Bar.meth, getattr, False, Bar, "meth") is None
    assert inspect.getdoc(Bar.meth, getattr, True, Bar, "meth") == Foo.meth.__doc__


def test_is_builtin_class_method():
    class MyInt(int):
        def my_method(self):
            pass

    assert inspect.is_builtin_class_method(MyInt, 'to_bytes')
    assert inspect.is_builtin_class_method(MyInt, '__init__')
    assert not inspect.is_builtin_class_method(MyInt, 'my_method')
    assert not inspect.is_builtin_class_method(MyInt, 'does_not_exist')
    assert not inspect.is_builtin_class_method(4, 'still does not crash')

    class ObjectWithMroAttr:
        def __init__(self, mro_attr):
            self.__mro__ = mro_attr

    assert not inspect.is_builtin_class_method(ObjectWithMroAttr([1, 2, 3]), 'still does not crash')
