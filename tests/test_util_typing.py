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
    assert stringify(int, False) == "int"
    assert stringify(int, True) == "int"

    assert stringify(str, False) == "str"
    assert stringify(str, True) == "str"

    assert stringify(None, False) == "None"
    assert stringify(None, True) == "None"

    assert stringify(Integral, False) == "numbers.Integral"
    assert stringify(Integral, True) == "~numbers.Integral"

    assert stringify(Struct, False) == "struct.Struct"
    assert stringify(Struct, True) == "~struct.Struct"

    assert stringify(TracebackType, False) == "types.TracebackType"
    assert stringify(TracebackType, True) == "~types.TracebackType"

    assert stringify(Any, False) == "Any"
    assert stringify(Any, True) == "~typing.Any"


def test_stringify_type_hints_containers():
    assert stringify(List, False) == "List"
    assert stringify(List, True) == "~typing.List"

    assert stringify(Dict, False) == "Dict"
    assert stringify(Dict, True) == "~typing.Dict"

    assert stringify(List[int], False) == "List[int]"
    assert stringify(List[int], True) == "~typing.List[int]"

    assert stringify(List[str], False) == "List[str]"
    assert stringify(List[str], True) == "~typing.List[str]"

    assert stringify(Dict[str, float], False) == "Dict[str, float]"
    assert stringify(Dict[str, float], True) == "~typing.Dict[str, float]"

    assert stringify(Tuple[str, str, str], False) == "Tuple[str, str, str]"
    assert stringify(Tuple[str, str, str], True) == "~typing.Tuple[str, str, str]"

    assert stringify(Tuple[str, ...], False) == "Tuple[str, ...]"
    assert stringify(Tuple[str, ...], True) == "~typing.Tuple[str, ...]"

    assert stringify(Tuple[()], False) == "Tuple[()]"
    assert stringify(Tuple[()], True) == "~typing.Tuple[()]"

    assert stringify(List[Dict[str, Tuple]], False) == "List[Dict[str, Tuple]]"
    assert stringify(List[Dict[str, Tuple]], True) == "~typing.List[~typing.Dict[str, ~typing.Tuple]]"

    assert stringify(MyList[Tuple[int, int]], False) == "tests.test_util_typing.MyList[Tuple[int, int]]"
    assert stringify(MyList[Tuple[int, int]], True) == "~tests.test_util_typing.MyList[~typing.Tuple[int, int]]"

    assert stringify(Generator[None, None, None], False) == "Generator[None, None, None]"
    assert stringify(Generator[None, None, None], True) == "~typing.Generator[None, None, None]"


@pytest.mark.skipif(sys.version_info < (3, 9), reason='python 3.9+ is required.')
def test_stringify_type_hints_pep_585():
    assert stringify(list[int], False) == "list[int]"
    assert stringify(list[int], True) == "list[int]"

    assert stringify(list[str], False) == "list[str]"
    assert stringify(list[str], True) == "list[str]"

    assert stringify(dict[str, float], False) == "dict[str, float]"
    assert stringify(dict[str, float], True) == "dict[str, float]"

    assert stringify(tuple[str, str, str], False) == "tuple[str, str, str]"
    assert stringify(tuple[str, str, str], True) == "tuple[str, str, str]"

    assert stringify(tuple[str, ...], False) == "tuple[str, ...]"
    assert stringify(tuple[str, ...], True) == "tuple[str, ...]"

    assert stringify(tuple[()], False) == "tuple[()]"
    assert stringify(tuple[()], True) == "tuple[()]"

    assert stringify(list[dict[str, tuple]], False) == "list[dict[str, tuple]]"
    assert stringify(list[dict[str, tuple]], True) == "list[dict[str, tuple]]"

    assert stringify(type[int], False) == "type[int]"
    assert stringify(type[int], True) == "type[int]"


@pytest.mark.skipif(sys.version_info < (3, 9), reason='python 3.9+ is required.')
def test_stringify_Annotated():
    from typing import Annotated  # type: ignore
    assert stringify(Annotated[str, "foo", "bar"], False) == "str"  # NOQA
    assert stringify(Annotated[str, "foo", "bar"], True) == "str"  # NOQA


def test_stringify_type_hints_string():
    assert stringify("int", False) == "int"
    assert stringify("int", True) == "int"

    assert stringify("str", False) == "str"
    assert stringify("str", True) == "str"

    assert stringify(List["int"], False) == "List[int]"
    assert stringify(List["int"], True) == "~typing.List[int]"

    assert stringify("Tuple[str]", False) == "Tuple[str]"
    assert stringify("Tuple[str]", True) == "Tuple[str]"

    assert stringify("unknown", False) == "unknown"
    assert stringify("unknown", True) == "unknown"


def test_stringify_type_hints_Callable():
    assert stringify(Callable, False) == "Callable"
    assert stringify(Callable, True) == "~typing.Callable"

    if sys.version_info >= (3, 7):
        assert stringify(Callable[[str], int], False) == "Callable[[str], int]"
        assert stringify(Callable[[str], int], True) == "~typing.Callable[[str], int]"

        assert stringify(Callable[..., int], False) == "Callable[[...], int]"
        assert stringify(Callable[..., int], True) == "~typing.Callable[[...], int]"
    else:
        assert stringify(Callable[[str], int], False) == "Callable[str, int]"
        assert stringify(Callable[[str], int], True) == "~typing.Callable[str, int]"

        assert stringify(Callable[..., int], False) == "Callable[..., int]"
        assert stringify(Callable[..., int], True) == "~typing.Callable[..., int]"


def test_stringify_type_hints_Union():
    assert stringify(Optional[int], False) == "Optional[int]"
    assert stringify(Optional[int], True) == "~typing.Optional[int]"

    assert stringify(Union[str, None], False) == "Optional[str]"
    assert stringify(Union[str, None], True) == "~typing.Optional[str]"

    assert stringify(Union[int, str], False) == "Union[int, str]"
    assert stringify(Union[int, str], True) == "~typing.Union[int, str]"

    if sys.version_info >= (3, 7):
        assert stringify(Union[int, Integral], False) == "Union[int, numbers.Integral]"
        assert stringify(Union[int, Integral], True) == "~typing.Union[int, ~numbers.Integral]"

        assert (stringify(Union[MyClass1, MyClass2], False) ==
                "Union[tests.test_util_typing.MyClass1, tests.test_util_typing.<MyClass2>]")
        assert (stringify(Union[MyClass1, MyClass2], True) ==
                "~typing.Union[~tests.test_util_typing.MyClass1, ~tests.test_util_typing.<MyClass2>]")
    else:
        assert stringify(Union[int, Integral], False) == "numbers.Integral"
        assert stringify(Union[int, Integral], True) == "~numbers.Integral"

        assert stringify(Union[MyClass1, MyClass2], False) == "tests.test_util_typing.MyClass1"
        assert stringify(Union[MyClass1, MyClass2], True) == "~tests.test_util_typing.MyClass1"


def test_stringify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    if sys.version_info < (3, 7):
        assert stringify(T, False) == "T"
        assert stringify(T, True) == "T"

        assert stringify(T_co, False) == "T_co"
        assert stringify(T_co, True) == "T_co"

        assert stringify(T_contra, False) == "T_contra"
        assert stringify(T_contra, True) == "T_contra"

        assert stringify(List[T], False) == "List[T]"
        assert stringify(List[T], True) == "~typing.List[T]"
    else:
        assert stringify(T, False) == "tests.test_util_typing.T"
        assert stringify(T, True) == "~tests.test_util_typing.T"

        assert stringify(T_co, False) == "tests.test_util_typing.T_co"
        assert stringify(T_co, True) == "~tests.test_util_typing.T_co"

        assert stringify(T_contra, False) == "tests.test_util_typing.T_contra"
        assert stringify(T_contra, True) == "~tests.test_util_typing.T_contra"

        assert stringify(List[T], False) == "List[tests.test_util_typing.T]"
        assert stringify(List[T], True) == "~typing.List[~tests.test_util_typing.T]"

    if sys.version_info >= (3, 10):
        assert stringify(MyInt, False) == "tests.test_util_typing.MyInt"
        assert stringify(MyInt, True) == "~tests.test_util_typing.MyInt"
    else:
        assert stringify(MyInt, False) == "MyInt"
        assert stringify(MyInt, True) == "MyInt"


def test_stringify_type_hints_custom_class():
    assert stringify(MyClass1, False) == "tests.test_util_typing.MyClass1"
    assert stringify(MyClass1, True) == "~tests.test_util_typing.MyClass1"

    assert stringify(MyClass2, False) == "tests.test_util_typing.<MyClass2>"
    assert stringify(MyClass2, True) == "~tests.test_util_typing.<MyClass2>"


def test_stringify_type_hints_alias():
    MyStr = str
    MyTuple = Tuple[str, str]

    assert stringify(MyStr, False) == "str"
    assert stringify(MyStr, True) == "str"

    assert stringify(MyTuple, False) == "Tuple[str, str]"  # type: ignore
    assert stringify(MyTuple, True) == "~typing.Tuple[str, str]"  # type: ignore


@pytest.mark.skipif(sys.version_info < (3, 8), reason='python 3.8+ is required.')
def test_stringify_type_Literal():
    from typing import Literal  # type: ignore
    assert stringify(Literal[1, "2", "\r"], False) == "Literal[1, '2', '\\r']"
    assert stringify(Literal[1, "2", "\r"], True) == "~typing.Literal[1, '2', '\\r']"


@pytest.mark.skipif(sys.version_info < (3, 10), reason='python 3.10+ is required.')
def test_stringify_type_union_operator():
    assert stringify(int | None, False) == "int | None"  # type: ignore
    assert stringify(int | None, True) == "int | None"  # type: ignore

    assert stringify(int | str, False) == "int | str"  # type: ignore
    assert stringify(int | str, True) == "int | str"  # type: ignore

    assert stringify(int | str | None, False) == "int | str | None"  # type: ignore
    assert stringify(int | str | None, True) == "int | str | None"  # type: ignore


def test_stringify_broken_type_hints():
    assert stringify(BrokenType, False) == 'tests.test_util_typing.BrokenType'
    assert stringify(BrokenType, True) == '~tests.test_util_typing.BrokenType'


def test_stringify_mock():
    with mock(['unknown']):
        import unknown
        assert stringify(unknown.secret.Class, False) == 'unknown.secret.Class'
        assert stringify(unknown.secret.Class, True) == 'unknown.secret.Class'
