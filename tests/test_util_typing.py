"""Tests util.typing functions."""

import sys
from numbers import Integral
from struct import Struct
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    List,
    NewType,
    Optional,
    Tuple,
    TypeVar,
    Union,
)

import pytest

from sphinx.ext.autodoc import mock
from sphinx.util.typing import restify, stringify_annotation


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
    assert restify(int, "smart") == ":py:class:`int`"

    assert restify(str) == ":py:class:`str`"
    assert restify(str, "smart") == ":py:class:`str`"

    assert restify(None) == ":py:obj:`None`"
    assert restify(None, "smart") == ":py:obj:`None`"

    assert restify(Integral) == ":py:class:`numbers.Integral`"
    assert restify(Integral, "smart") == ":py:class:`~numbers.Integral`"

    assert restify(Struct) == ":py:class:`struct.Struct`"
    assert restify(Struct, "smart") == ":py:class:`~struct.Struct`"

    assert restify(TracebackType) == ":py:class:`types.TracebackType`"
    assert restify(TracebackType, "smart") == ":py:class:`~types.TracebackType`"

    assert restify(Any) == ":py:obj:`~typing.Any`"
    assert restify(Any, "smart") == ":py:obj:`~typing.Any`"

    assert restify('str') == "str"
    assert restify('str', "smart") == "str"


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

    if sys.version_info[:2] <= (3, 10):
        assert restify(Tuple[()]) == ":py:class:`~typing.Tuple`\\ [()]"
    else:
        assert restify(Tuple[()]) == ":py:class:`~typing.Tuple`"

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

    assert restify(Callable[[str], int]) == (":py:class:`~typing.Callable`\\ "
                                             "[[:py:class:`str`], :py:class:`int`]")
    assert restify(Callable[..., int]) == (":py:class:`~typing.Callable`\\ "
                                           "[[...], :py:class:`int`]")


def test_restify_type_hints_Union():
    assert restify(Optional[int]) == ":py:obj:`~typing.Optional`\\ [:py:class:`int`]"
    assert restify(Union[str, None]) == ":py:obj:`~typing.Optional`\\ [:py:class:`str`]"
    assert restify(Union[int, str]) == (":py:obj:`~typing.Union`\\ "
                                        "[:py:class:`int`, :py:class:`str`]")
    assert restify(Union[int, Integral]) == (":py:obj:`~typing.Union`\\ "
                                             "[:py:class:`int`, :py:class:`numbers.Integral`]")
    assert restify(Union[int, Integral], "smart") == (":py:obj:`~typing.Union`\\ "
                                                      "[:py:class:`int`,"
                                                      " :py:class:`~numbers.Integral`]")

    assert (restify(Union[MyClass1, MyClass2]) ==
            (":py:obj:`~typing.Union`\\ "
             "[:py:class:`tests.test_util_typing.MyClass1`, "
             ":py:class:`tests.test_util_typing.<MyClass2>`]"))
    assert (restify(Union[MyClass1, MyClass2], "smart") ==
            (":py:obj:`~typing.Union`\\ "
             "[:py:class:`~tests.test_util_typing.MyClass1`,"
             " :py:class:`~tests.test_util_typing.<MyClass2>`]"))


def test_restify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    assert restify(T) == ":py:obj:`tests.test_util_typing.T`"
    assert restify(T, "smart") == ":py:obj:`~tests.test_util_typing.T`"

    assert restify(T_co) == ":py:obj:`tests.test_util_typing.T_co`"
    assert restify(T_co, "smart") == ":py:obj:`~tests.test_util_typing.T_co`"

    assert restify(T_contra) == ":py:obj:`tests.test_util_typing.T_contra`"
    assert restify(T_contra, "smart") == ":py:obj:`~tests.test_util_typing.T_contra`"

    assert restify(List[T]) == ":py:class:`~typing.List`\\ [:py:obj:`tests.test_util_typing.T`]"
    assert restify(List[T], "smart") == ":py:class:`~typing.List`\\ [:py:obj:`~tests.test_util_typing.T`]"

    if sys.version_info[:2] >= (3, 10):
        assert restify(MyInt) == ":py:class:`tests.test_util_typing.MyInt`"
        assert restify(MyInt, "smart") == ":py:class:`~tests.test_util_typing.MyInt`"
    else:
        assert restify(MyInt) == ":py:class:`MyInt`"
        assert restify(MyInt, "smart") == ":py:class:`MyInt`"


def test_restify_type_hints_custom_class():
    assert restify(MyClass1) == ":py:class:`tests.test_util_typing.MyClass1`"
    assert restify(MyClass1, "smart") == ":py:class:`~tests.test_util_typing.MyClass1`"

    assert restify(MyClass2) == ":py:class:`tests.test_util_typing.<MyClass2>`"
    assert restify(MyClass2, "smart") == ":py:class:`~tests.test_util_typing.<MyClass2>`"


def test_restify_type_hints_alias():
    MyStr = str
    MyTuple = Tuple[str, str]
    assert restify(MyStr) == ":py:class:`str`"
    assert restify(MyTuple) == ":py:class:`~typing.Tuple`\\ [:py:class:`str`, :py:class:`str`]"


def test_restify_type_ForwardRef():
    from typing import ForwardRef  # type: ignore
    assert restify(ForwardRef("myint")) == ":py:class:`myint`"  # NoQA: F821


def test_restify_type_Literal():
    from typing import Literal  # type: ignore
    assert restify(Literal[1, "2", "\r"]) == ":py:obj:`~typing.Literal`\\ [1, '2', '\\r']"


@pytest.mark.skipif(sys.version_info[:2] <= (3, 8), reason='python 3.9+ is required.')
def test_restify_pep_585():
    assert restify(list[str]) == ":py:class:`list`\\ [:py:class:`str`]"  # type: ignore
    assert restify(dict[str, str]) == (":py:class:`dict`\\ "  # type: ignore
                                       "[:py:class:`str`, :py:class:`str`]")
    assert restify(dict[str, tuple[int, ...]]) == (":py:class:`dict`\\ "  # type: ignore
                                                   "[:py:class:`str`, :py:class:`tuple`\\ "
                                                   "[:py:class:`int`, ...]]")


@pytest.mark.skipif(sys.version_info[:2] <= (3, 9), reason='python 3.10+ is required.')
def test_restify_type_union_operator():
    assert restify(int | None) == ":py:class:`int` | :py:obj:`None`"  # type: ignore
    assert restify(int | str) == ":py:class:`int` | :py:class:`str`"  # type: ignore
    assert restify(int | str | None) == (":py:class:`int` | :py:class:`str` | "  # type: ignore
                                         ":py:obj:`None`")


def test_restify_broken_type_hints():
    assert restify(BrokenType) == ':py:class:`tests.test_util_typing.BrokenType`'
    assert restify(BrokenType, "smart") == ':py:class:`~tests.test_util_typing.BrokenType`'


def test_restify_mock():
    with mock(['unknown']):
        import unknown
        assert restify(unknown) == ':py:class:`unknown`'
        assert restify(unknown.secret.Class) == ':py:class:`unknown.secret.Class`'
        assert restify(unknown.secret.Class, "smart") == ':py:class:`~unknown.secret.Class`'


def test_stringify_annotation():
    assert stringify_annotation(int, 'fully-qualified-except-typing') == "int"
    assert stringify_annotation(int, "smart") == "int"

    assert stringify_annotation(str, 'fully-qualified-except-typing') == "str"
    assert stringify_annotation(str, "smart") == "str"

    assert stringify_annotation(None, 'fully-qualified-except-typing') == "None"
    assert stringify_annotation(None, "smart") == "None"

    assert stringify_annotation(Integral, 'fully-qualified-except-typing') == "numbers.Integral"
    assert stringify_annotation(Integral, "smart") == "~numbers.Integral"

    assert stringify_annotation(Struct, 'fully-qualified-except-typing') == "struct.Struct"
    assert stringify_annotation(Struct, "smart") == "~struct.Struct"

    assert stringify_annotation(TracebackType, 'fully-qualified-except-typing') == "types.TracebackType"
    assert stringify_annotation(TracebackType, "smart") == "~types.TracebackType"

    assert stringify_annotation(Any, 'fully-qualified-except-typing') == "Any"
    assert stringify_annotation(Any, "fully-qualified") == "typing.Any"
    assert stringify_annotation(Any, "smart") == "~typing.Any"


def test_stringify_type_hints_containers():
    assert stringify_annotation(List, 'fully-qualified-except-typing') == "List"
    assert stringify_annotation(List, "fully-qualified") == "typing.List"
    assert stringify_annotation(List, "smart") == "~typing.List"

    assert stringify_annotation(Dict, 'fully-qualified-except-typing') == "Dict"
    assert stringify_annotation(Dict, "fully-qualified") == "typing.Dict"
    assert stringify_annotation(Dict, "smart") == "~typing.Dict"

    assert stringify_annotation(List[int], 'fully-qualified-except-typing') == "List[int]"
    assert stringify_annotation(List[int], "fully-qualified") == "typing.List[int]"
    assert stringify_annotation(List[int], "smart") == "~typing.List[int]"

    assert stringify_annotation(List[str], 'fully-qualified-except-typing') == "List[str]"
    assert stringify_annotation(List[str], "fully-qualified") == "typing.List[str]"
    assert stringify_annotation(List[str], "smart") == "~typing.List[str]"

    assert stringify_annotation(Dict[str, float], 'fully-qualified-except-typing') == "Dict[str, float]"
    assert stringify_annotation(Dict[str, float], "fully-qualified") == "typing.Dict[str, float]"
    assert stringify_annotation(Dict[str, float], "smart") == "~typing.Dict[str, float]"

    assert stringify_annotation(Tuple[str, str, str], 'fully-qualified-except-typing') == "Tuple[str, str, str]"
    assert stringify_annotation(Tuple[str, str, str], "fully-qualified") == "typing.Tuple[str, str, str]"
    assert stringify_annotation(Tuple[str, str, str], "smart") == "~typing.Tuple[str, str, str]"

    assert stringify_annotation(Tuple[str, ...], 'fully-qualified-except-typing') == "Tuple[str, ...]"
    assert stringify_annotation(Tuple[str, ...], "fully-qualified") == "typing.Tuple[str, ...]"
    assert stringify_annotation(Tuple[str, ...], "smart") == "~typing.Tuple[str, ...]"

    if sys.version_info[:2] <= (3, 10):
        assert stringify_annotation(Tuple[()], 'fully-qualified-except-typing') == "Tuple[()]"
        assert stringify_annotation(Tuple[()], "fully-qualified") == "typing.Tuple[()]"
        assert stringify_annotation(Tuple[()], "smart") == "~typing.Tuple[()]"
    else:
        assert stringify_annotation(Tuple[()], 'fully-qualified-except-typing') == "Tuple"
        assert stringify_annotation(Tuple[()], "fully-qualified") == "typing.Tuple"
        assert stringify_annotation(Tuple[()], "smart") == "~typing.Tuple"

    assert stringify_annotation(List[Dict[str, Tuple]], 'fully-qualified-except-typing') == "List[Dict[str, Tuple]]"
    assert stringify_annotation(List[Dict[str, Tuple]], "fully-qualified") == "typing.List[typing.Dict[str, typing.Tuple]]"
    assert stringify_annotation(List[Dict[str, Tuple]], "smart") == "~typing.List[~typing.Dict[str, ~typing.Tuple]]"

    assert stringify_annotation(MyList[Tuple[int, int]], 'fully-qualified-except-typing') == "tests.test_util_typing.MyList[Tuple[int, int]]"
    assert stringify_annotation(MyList[Tuple[int, int]], "fully-qualified") == "tests.test_util_typing.MyList[typing.Tuple[int, int]]"
    assert stringify_annotation(MyList[Tuple[int, int]], "smart") == "~tests.test_util_typing.MyList[~typing.Tuple[int, int]]"

    assert stringify_annotation(Generator[None, None, None], 'fully-qualified-except-typing') == "Generator[None, None, None]"
    assert stringify_annotation(Generator[None, None, None], "fully-qualified") == "typing.Generator[None, None, None]"
    assert stringify_annotation(Generator[None, None, None], "smart") == "~typing.Generator[None, None, None]"


@pytest.mark.skipif(sys.version_info[:2] <= (3, 8), reason='python 3.9+ is required.')
def test_stringify_type_hints_pep_585():
    assert stringify_annotation(list[int], 'fully-qualified-except-typing') == "list[int]"
    assert stringify_annotation(list[int], "smart") == "list[int]"

    assert stringify_annotation(list[str], 'fully-qualified-except-typing') == "list[str]"
    assert stringify_annotation(list[str], "smart") == "list[str]"

    assert stringify_annotation(dict[str, float], 'fully-qualified-except-typing') == "dict[str, float]"
    assert stringify_annotation(dict[str, float], "smart") == "dict[str, float]"

    assert stringify_annotation(tuple[str, str, str], 'fully-qualified-except-typing') == "tuple[str, str, str]"
    assert stringify_annotation(tuple[str, str, str], "smart") == "tuple[str, str, str]"

    assert stringify_annotation(tuple[str, ...], 'fully-qualified-except-typing') == "tuple[str, ...]"
    assert stringify_annotation(tuple[str, ...], "smart") == "tuple[str, ...]"

    assert stringify_annotation(tuple[()], 'fully-qualified-except-typing') == "tuple[()]"
    assert stringify_annotation(tuple[()], "smart") == "tuple[()]"

    assert stringify_annotation(list[dict[str, tuple]], 'fully-qualified-except-typing') == "list[dict[str, tuple]]"
    assert stringify_annotation(list[dict[str, tuple]], "smart") == "list[dict[str, tuple]]"

    assert stringify_annotation(type[int], 'fully-qualified-except-typing') == "type[int]"
    assert stringify_annotation(type[int], "smart") == "type[int]"


@pytest.mark.skipif(sys.version_info[:2] <= (3, 8), reason='python 3.9+ is required.')
def test_stringify_Annotated():
    from typing import Annotated  # type: ignore
    assert stringify_annotation(Annotated[str, "foo", "bar"], 'fully-qualified-except-typing') == "str"
    assert stringify_annotation(Annotated[str, "foo", "bar"], "smart") == "str"


def test_stringify_type_hints_string():
    assert stringify_annotation("int", 'fully-qualified-except-typing') == "int"
    assert stringify_annotation("int", 'fully-qualified') == "int"
    assert stringify_annotation("int", "smart") == "int"

    assert stringify_annotation("str", 'fully-qualified-except-typing') == "str"
    assert stringify_annotation("str", 'fully-qualified') == "str"
    assert stringify_annotation("str", "smart") == "str"

    assert stringify_annotation(List["int"], 'fully-qualified-except-typing') == "List[int]"
    assert stringify_annotation(List["int"], 'fully-qualified') == "typing.List[int]"
    assert stringify_annotation(List["int"], "smart") == "~typing.List[int]"

    assert stringify_annotation("Tuple[str]", 'fully-qualified-except-typing') == "Tuple[str]"
    assert stringify_annotation("Tuple[str]", 'fully-qualified') == "Tuple[str]"
    assert stringify_annotation("Tuple[str]", "smart") == "Tuple[str]"

    assert stringify_annotation("unknown", 'fully-qualified-except-typing') == "unknown"
    assert stringify_annotation("unknown", 'fully-qualified') == "unknown"
    assert stringify_annotation("unknown", "smart") == "unknown"


def test_stringify_type_hints_Callable():
    assert stringify_annotation(Callable, 'fully-qualified-except-typing') == "Callable"
    assert stringify_annotation(Callable, "fully-qualified") == "typing.Callable"
    assert stringify_annotation(Callable, "smart") == "~typing.Callable"

    assert stringify_annotation(Callable[[str], int], 'fully-qualified-except-typing') == "Callable[[str], int]"
    assert stringify_annotation(Callable[[str], int], "fully-qualified") == "typing.Callable[[str], int]"
    assert stringify_annotation(Callable[[str], int], "smart") == "~typing.Callable[[str], int]"

    assert stringify_annotation(Callable[..., int], 'fully-qualified-except-typing') == "Callable[[...], int]"
    assert stringify_annotation(Callable[..., int], "fully-qualified") == "typing.Callable[[...], int]"
    assert stringify_annotation(Callable[..., int], "smart") == "~typing.Callable[[...], int]"


def test_stringify_type_hints_Union():
    assert stringify_annotation(Optional[int], 'fully-qualified-except-typing') == "int | None"
    assert stringify_annotation(Optional[int], "fully-qualified") == "int | None"
    assert stringify_annotation(Optional[int], "smart") == "int | None"

    assert stringify_annotation(Union[str, None], 'fully-qualified-except-typing') == "str | None"
    assert stringify_annotation(Union[str, None], "fully-qualified") == "str | None"
    assert stringify_annotation(Union[str, None], "smart") == "str | None"

    assert stringify_annotation(Union[int, str], 'fully-qualified-except-typing') == "int | str"
    assert stringify_annotation(Union[int, str], "fully-qualified") == "int | str"
    assert stringify_annotation(Union[int, str], "smart") == "int | str"

    assert stringify_annotation(Union[int, Integral], 'fully-qualified-except-typing') == "int | numbers.Integral"
    assert stringify_annotation(Union[int, Integral], "fully-qualified") == "int | numbers.Integral"
    assert stringify_annotation(Union[int, Integral], "smart") == "int | ~numbers.Integral"

    assert (stringify_annotation(Union[MyClass1, MyClass2], 'fully-qualified-except-typing') ==
            "tests.test_util_typing.MyClass1 | tests.test_util_typing.<MyClass2>")
    assert (stringify_annotation(Union[MyClass1, MyClass2], "fully-qualified") ==
            "tests.test_util_typing.MyClass1 | tests.test_util_typing.<MyClass2>")
    assert (stringify_annotation(Union[MyClass1, MyClass2], "smart") ==
            "~tests.test_util_typing.MyClass1 | ~tests.test_util_typing.<MyClass2>")


def test_stringify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    assert stringify_annotation(T, 'fully-qualified-except-typing') == "tests.test_util_typing.T"
    assert stringify_annotation(T, "smart") == "~tests.test_util_typing.T"

    assert stringify_annotation(T_co, 'fully-qualified-except-typing') == "tests.test_util_typing.T_co"
    assert stringify_annotation(T_co, "smart") == "~tests.test_util_typing.T_co"

    assert stringify_annotation(T_contra, 'fully-qualified-except-typing') == "tests.test_util_typing.T_contra"
    assert stringify_annotation(T_contra, "smart") == "~tests.test_util_typing.T_contra"

    assert stringify_annotation(List[T], 'fully-qualified-except-typing') == "List[tests.test_util_typing.T]"
    assert stringify_annotation(List[T], "smart") == "~typing.List[~tests.test_util_typing.T]"

    if sys.version_info[:2] >= (3, 10):
        assert stringify_annotation(MyInt, 'fully-qualified-except-typing') == "tests.test_util_typing.MyInt"
        assert stringify_annotation(MyInt, "smart") == "~tests.test_util_typing.MyInt"
    else:
        assert stringify_annotation(MyInt, 'fully-qualified-except-typing') == "MyInt"
        assert stringify_annotation(MyInt, "smart") == "MyInt"


def test_stringify_type_hints_custom_class():
    assert stringify_annotation(MyClass1, 'fully-qualified-except-typing') == "tests.test_util_typing.MyClass1"
    assert stringify_annotation(MyClass1, "smart") == "~tests.test_util_typing.MyClass1"

    assert stringify_annotation(MyClass2, 'fully-qualified-except-typing') == "tests.test_util_typing.<MyClass2>"
    assert stringify_annotation(MyClass2, "smart") == "~tests.test_util_typing.<MyClass2>"


def test_stringify_type_hints_alias():
    MyStr = str
    MyTuple = Tuple[str, str]

    assert stringify_annotation(MyStr, 'fully-qualified-except-typing') == "str"
    assert stringify_annotation(MyStr, "smart") == "str"

    assert stringify_annotation(MyTuple) == "Tuple[str, str]"  # type: ignore
    assert stringify_annotation(MyTuple, "smart") == "~typing.Tuple[str, str]"  # type: ignore


def test_stringify_type_Literal():
    from typing import Literal  # type: ignore
    assert stringify_annotation(Literal[1, "2", "\r"], 'fully-qualified-except-typing') == "Literal[1, '2', '\\r']"
    assert stringify_annotation(Literal[1, "2", "\r"], "fully-qualified") == "typing.Literal[1, '2', '\\r']"
    assert stringify_annotation(Literal[1, "2", "\r"], "smart") == "~typing.Literal[1, '2', '\\r']"


@pytest.mark.skipif(sys.version_info[:2] <= (3, 9), reason='python 3.10+ is required.')
def test_stringify_type_union_operator():
    assert stringify_annotation(int | None) == "int | None"  # type: ignore
    assert stringify_annotation(int | None, "smart") == "int | None"  # type: ignore

    assert stringify_annotation(int | str) == "int | str"  # type: ignore
    assert stringify_annotation(int | str, "smart") == "int | str"  # type: ignore

    assert stringify_annotation(int | str | None) == "int | str | None"  # type: ignore
    assert stringify_annotation(int | str | None, "smart") == "int | str | None"  # type: ignore


def test_stringify_broken_type_hints():
    assert stringify_annotation(BrokenType, 'fully-qualified-except-typing') == 'tests.test_util_typing.BrokenType'
    assert stringify_annotation(BrokenType, "smart") == '~tests.test_util_typing.BrokenType'


def test_stringify_mock():
    with mock(['unknown']):
        import unknown
        assert stringify_annotation(unknown, 'fully-qualified-except-typing') == 'unknown'
        assert stringify_annotation(unknown.secret.Class, 'fully-qualified-except-typing') == 'unknown.secret.Class'
        assert stringify_annotation(unknown.secret.Class, "smart") == 'unknown.secret.Class'
