"""
    test_util_typing
    ~~~~~~~~~~~~~~~~

    Tests util.typing functions.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from numbers import Integral
from struct import Struct
from types import TracebackType
from typing import (Any, Callable, Dict, Generator, List, NewType, Optional, Tuple, TypeVar,
                    Union)

import pytest

from sphinx.ext.autodoc import mock
from sphinx.util.typing import restify, stringify


class MyClass1:
    pass


class MyClass2(MyClass1):
    __qualname__ = '<MyClass2>'


T = TypeVar('T')
MyInt = NewType('MyInt', int)


class MyList(List[T]):
    pass


class BrokenType:
    __args__ = int


def test_restify():
    assert restify(int) == ":py:class:`int`"
    assert restify(str) == ":py:class:`str`"
    assert restify(None) == ":py:obj:`None`"
    assert restify(Integral) == ":py:class:`numbers.Integral`"
    assert restify(Struct) == ":py:class:`struct.Struct`"
    assert restify(TracebackType) == ":py:class:`types.TracebackType`"
    assert restify(Any) == ":py:obj:`~typing.Any`"
    assert restify('str') == "str"


def test_restify_type_hints_containers():
    assert restify(List) == ":py:class:`~typing.List`"
    assert restify(Dict) == ":py:class:`~typing.Dict`"
    assert restify(List[int]) == ":py:class:`~typing.List`\\ [:py:class:`int`]"
    assert restify(List[str]) == ":py:class:`~typing.List`\\ [:py:class:`str`]"
    assert restify(Dict[str, float]) == (":py:class:`~typing.Dict`\\ "
                                         "[:py:class:`str`, :py:class:`float`]")
    assert restify(Tuple[str, str, str]) == (":py:class:`~typing.Tuple`\\ "
                                             "[:py:class:`str`, :py:class:`str`, "
                                             ":py:class:`str`]")
    assert restify(Tuple[str, ...]) == ":py:class:`~typing.Tuple`\\ [:py:class:`str`, ...]"
    assert restify(Tuple[()]) == ":py:class:`~typing.Tuple`\\ [()]"
    assert restify(List[Dict[str, Tuple]]) == (":py:class:`~typing.List`\\ "
                                               "[:py:class:`~typing.Dict`\\ "
                                               "[:py:class:`str`, :py:class:`~typing.Tuple`]]")
    assert restify(MyList[Tuple[int, int]]) == (":py:class:`tests.test_util_typing.MyList`\\ "
                                                "[:py:class:`~typing.Tuple`\\ "
                                                "[:py:class:`int`, :py:class:`int`]]")
    assert restify(Generator[None, None, None]) == (":py:class:`~typing.Generator`\\ "
                                                    "[:py:obj:`None`, :py:obj:`None`, "
                                                    ":py:obj:`None`]")


def test_restify_type_hints_Callable():
    assert restify(Callable) == ":py:class:`~typing.Callable`"

    if sys.version_info >= (3, 7):
        assert restify(Callable[[str], int]) == (":py:class:`~typing.Callable`\\ "
                                                 "[[:py:class:`str`], :py:class:`int`]")
        assert restify(Callable[..., int]) == (":py:class:`~typing.Callable`\\ "
                                               "[[...], :py:class:`int`]")
    else:
        assert restify(Callable[[str], int]) == (":py:class:`~typing.Callable`\\ "
                                                 "[:py:class:`str`, :py:class:`int`]")
        assert restify(Callable[..., int]) == (":py:class:`~typing.Callable`\\ "
                                               "[..., :py:class:`int`]")


def test_restify_type_hints_Union():
    assert restify(Optional[int]) == ":py:obj:`~typing.Optional`\\ [:py:class:`int`]"
    assert restify(Union[str, None]) == ":py:obj:`~typing.Optional`\\ [:py:class:`str`]"
    assert restify(Union[int, str]) == (":py:obj:`~typing.Union`\\ "
                                        "[:py:class:`int`, :py:class:`str`]")

    if sys.version_info >= (3, 7):
        assert restify(Union[int, Integral]) == (":py:obj:`~typing.Union`\\ "
                                                 "[:py:class:`int`, :py:class:`numbers.Integral`]")
        assert (restify(Union[MyClass1, MyClass2]) ==
                (":py:obj:`~typing.Union`\\ "
                 "[:py:class:`tests.test_util_typing.MyClass1`, "
                 ":py:class:`tests.test_util_typing.<MyClass2>`]"))
    else:
        assert restify(Union[int, Integral]) == ":py:class:`numbers.Integral`"
        assert restify(Union[MyClass1, MyClass2]) == ":py:class:`tests.test_util_typing.MyClass1`"


@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required.')
def test_restify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    assert restify(T) == ":py:obj:`tests.test_util_typing.T`"
    assert restify(T_co) == ":py:obj:`tests.test_util_typing.T_co`"
    assert restify(T_contra) == ":py:obj:`tests.test_util_typing.T_contra`"
    assert restify(List[T]) == ":py:class:`~typing.List`\\ [:py:obj:`tests.test_util_typing.T`]"

    if sys.version_info >= (3, 10):
        assert restify(MyInt) == ":py:class:`tests.test_util_typing.MyInt`"
    else:
        assert restify(MyInt) == ":py:class:`MyInt`"


def test_restify_type_hints_custom_class():
    assert restify(MyClass1) == ":py:class:`tests.test_util_typing.MyClass1`"
    assert restify(MyClass2) == ":py:class:`tests.test_util_typing.<MyClass2>`"


def test_restify_type_hints_alias():
    MyStr = str
    MyTuple = Tuple[str, str]
    assert restify(MyStr) == ":py:class:`str`"
    assert restify(MyTuple) == ":py:class:`~typing.Tuple`\\ [:py:class:`str`, :py:class:`str`]"


@pytest.mark.skipif(sys.version_info < (3, 7), reason='python 3.7+ is required.')
def test_restify_type_ForwardRef():
    from typing import ForwardRef  # type: ignore
    assert restify(ForwardRef("myint")) == ":py:class:`myint`"


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
def test_restify_type_Literal():
    from typing import Literal  # type: ignore
    assert restify(Literal[1, "2", "\r"]) == ":py:obj:`~typing.Literal`\\ [1, '2', '\\r']"


@pytest.mark.skipif(sys.version_info < (3, 9), reason='python 3.9+ is required.')
def test_restify_pep_585():
    assert restify(list[str]) == ":py:class:`list`\\ [:py:class:`str`]"  # type: ignore
    assert restify(dict[str, str]) == (":py:class:`dict`\\ "  # type: ignore
                                       "[:py:class:`str`, :py:class:`str`]")
    assert restify(dict[str, tuple[int, ...]]) == (":py:class:`dict`\\ "  # type: ignore
                                                   "[:py:class:`str`, :py:class:`tuple`\\ "
                                                   "[:py:class:`int`, ...]]")


@pytest.mark.skipif(sys.version_info < (3, 10), reason='python 3.10+ is required.')
def test_restify_type_union_operator():
    assert restify(int | None) == ":py:class:`int` | :py:obj:`None`"  # type: ignore
    assert restify(int | str) == ":py:class:`int` | :py:class:`str`"  # type: ignore
    assert restify(int | str | None) == (":py:class:`int` | :py:class:`str` | "  # type: ignore
                                         ":py:obj:`None`")


def test_restify_broken_type_hints():
    assert restify(BrokenType) == ':py:class:`tests.test_util_typing.BrokenType`'


def test_restify_mock():
    with mock(['unknown']):
        import unknown
        assert restify(unknown.secret.Class) == ':py:class:`unknown.secret.Class`'


def test_stringify():
    assert stringify(int) == "int"
    assert stringify(str) == "str"
    assert stringify(None) == "None"
    assert stringify(Integral) == "numbers.Integral"
    assert stringify(Struct) == "struct.Struct"
    assert stringify(TracebackType) == "types.TracebackType"
    assert stringify(Any) == "Any"


def test_stringify_type_hints_containers():
    assert stringify(List) == "List"
    assert stringify(Dict) == "Dict"
    assert stringify(List[int]) == "List[int]"
    assert stringify(List[str]) == "List[str]"
    assert stringify(Dict[str, float]) == "Dict[str, float]"
    assert stringify(Tuple[str, str, str]) == "Tuple[str, str, str]"
    assert stringify(Tuple[str, ...]) == "Tuple[str, ...]"
    assert stringify(Tuple[()]) == "Tuple[()]"
    assert stringify(List[Dict[str, Tuple]]) == "List[Dict[str, Tuple]]"
    assert stringify(MyList[Tuple[int, int]]) == "tests.test_util_typing.MyList[Tuple[int, int]]"
    assert stringify(Generator[None, None, None]) == "Generator[None, None, None]"


@pytest.mark.skipif(sys.version_info < (3, 9), reason='python 3.9+ is required.')
def test_stringify_type_hints_pep_585():
    assert stringify(list[int]) == "list[int]"
    assert stringify(list[str]) == "list[str]"
    assert stringify(dict[str, float]) == "dict[str, float]"
    assert stringify(tuple[str, str, str]) == "tuple[str, str, str]"
    assert stringify(tuple[str, ...]) == "tuple[str, ...]"
    assert stringify(tuple[()]) == "tuple[()]"
    assert stringify(list[dict[str, tuple]]) == "list[dict[str, tuple]]"
    assert stringify(type[int]) == "type[int]"


@pytest.mark.skipif(sys.version_info < (3, 9), reason='python 3.9+ is required.')
def test_stringify_Annotated():
    from typing import Annotated  # type: ignore
    assert stringify(Annotated[str, "foo", "bar"]) == "str"  # NOQA


def test_stringify_type_hints_string():
    assert stringify("int") == "int"
    assert stringify("str") == "str"
    assert stringify(List["int"]) == "List[int]"
    assert stringify("Tuple[str]") == "Tuple[str]"
    assert stringify("unknown") == "unknown"


def test_stringify_type_hints_Callable():
    assert stringify(Callable) == "Callable"

    if sys.version_info >= (3, 7):
        assert stringify(Callable[[str], int]) == "Callable[[str], int]"
        assert stringify(Callable[..., int]) == "Callable[[...], int]"
    else:
        assert stringify(Callable[[str], int]) == "Callable[str, int]"
        assert stringify(Callable[..., int]) == "Callable[..., int]"


def test_stringify_type_hints_Union():
    assert stringify(Optional[int]) == "Optional[int]"
    assert stringify(Union[str, None]) == "Optional[str]"
    assert stringify(Union[int, str]) == "Union[int, str]"

    if sys.version_info >= (3, 7):
        assert stringify(Union[int, Integral]) == "Union[int, numbers.Integral]"
        assert (stringify(Union[MyClass1, MyClass2]) ==
                "Union[tests.test_util_typing.MyClass1, tests.test_util_typing.<MyClass2>]")
    else:
        assert stringify(Union[int, Integral]) == "numbers.Integral"
        assert stringify(Union[MyClass1, MyClass2]) == "tests.test_util_typing.MyClass1"


def test_stringify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    if sys.version_info < (3, 7):
        assert stringify(T) == "T"
        assert stringify(T_co) == "T_co"
        assert stringify(T_contra) == "T_contra"
        assert stringify(List[T]) == "List[T]"
    else:
        assert stringify(T) == "tests.test_util_typing.T"
        assert stringify(T_co) == "tests.test_util_typing.T_co"
        assert stringify(T_contra) == "tests.test_util_typing.T_contra"
        assert stringify(List[T]) == "List[tests.test_util_typing.T]"

    if sys.version_info >= (3, 10):
        assert stringify(MyInt) == "tests.test_util_typing.MyInt"
    else:
        assert stringify(MyInt) == "MyInt"


def test_stringify_type_hints_custom_class():
    assert stringify(MyClass1) == "tests.test_util_typing.MyClass1"
    assert stringify(MyClass2) == "tests.test_util_typing.<MyClass2>"


def test_stringify_type_hints_alias():
    MyStr = str
    MyTuple = Tuple[str, str]
    assert stringify(MyStr) == "str"
    assert stringify(MyTuple) == "Tuple[str, str]"  # type: ignore


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
def test_stringify_type_Literal():
    from typing import Literal  # type: ignore
    assert stringify(Literal[1, "2", "\r"]) == "Literal[1, '2', '\\r']"


@pytest.mark.skipif(sys.version_info < (3, 10), reason='python 3.10+ is required.')
def test_stringify_type_union_operator():
    assert stringify(int | None) == "int | None"  # type: ignore
    assert stringify(int | str) == "int | str"  # type: ignore
    assert stringify(int | str | None) == "int | str | None"  # type: ignore


def test_stringify_broken_type_hints():
    assert stringify(BrokenType) == 'tests.test_util_typing.BrokenType'


def test_stringify_mock():
    with mock(['unknown']):
        import unknown
        assert stringify(unknown.secret.Class) == 'unknown.secret.Class'
