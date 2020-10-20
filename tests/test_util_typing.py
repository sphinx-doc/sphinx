"""
    test_util_typing
    ~~~~~~~~~~~~~~~~

    Tests util.typing functions.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from numbers import Integral
from typing import (
    Any, Dict, Generator, List, TypeVar, Union, Callable, Tuple, Optional, Generic
)

import pytest

from sphinx.util.typing import stringify


class MyClass1:
    pass


class MyClass2(MyClass1):
    __qualname__ = '<MyClass2>'

T = TypeVar('T')

class MyList(List[T]):
    pass


class BrokenType:
    __args__ = int


def test_stringify():
    assert stringify(int) == "int"
    assert stringify(str) == "str"
    assert stringify(None) == "None"
    assert stringify(Integral) == "numbers.Integral"
    assert stringify(Any) == "Any"


def test_stringify_type_hints_containers():
    assert stringify(List) == "List"
    assert stringify(Dict) == "Dict"
    assert stringify(List[int]) == "List[int]"
    assert stringify(List[str]) == "List[str]"
    assert stringify(Dict[str, float]) == "Dict[str, float]"
    assert stringify(Tuple[str, str, str]) == "Tuple[str, str, str]"
    assert stringify(Tuple[str, ...]) == "Tuple[str, ...]"
    assert stringify(List[Dict[str, Tuple]]) == "List[Dict[str, Tuple]]"
    assert stringify(MyList[Tuple[int, int]]) == "test_util_typing.MyList[Tuple[int, int]]"
    assert stringify(Generator[None, None, None]) == "Generator[None, None, None]"


@pytest.mark.skipif(sys.version_info < (3, 9), reason='python 3.9+ is required.')
def test_stringify_Annotated():
    from typing import Annotated
    assert stringify(Annotated[str, "foo", "bar"]) == "str"


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
                "Union[test_util_typing.MyClass1, test_util_typing.<MyClass2>]")
    else:
        assert stringify(Union[int, Integral]) == "numbers.Integral"
        assert stringify(Union[MyClass1, MyClass2]) == "test_util_typing.MyClass1"


def test_stringify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    assert stringify(T) == "T"
    assert stringify(T_co) == "T_co"
    assert stringify(T_contra) == "T_contra"
    assert stringify(List[T]) == "List[T]"


def test_stringify_type_hints_custom_class():
    assert stringify(MyClass1) == "test_util_typing.MyClass1"
    assert stringify(MyClass2) == "test_util_typing.<MyClass2>"


def test_stringify_type_hints_alias():
    MyStr = str
    MyTuple = Tuple[str, str]
    assert stringify(MyStr) == "str"
    assert stringify(MyTuple) == "Tuple[str, str]"  # type: ignore


def test_stringify_broken_type_hints():
    assert stringify(BrokenType) == 'test_util_typing.BrokenType'
