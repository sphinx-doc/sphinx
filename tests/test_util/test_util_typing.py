"""Tests util.typing functions."""

from __future__ import annotations

import ctypes
import dataclasses
import sys
import typing as t
import zipfile
from collections import abc
from contextvars import Context, ContextVar, Token
from enum import Enum
from io import (
    BufferedRandom,
    BufferedReader,
    BufferedRWPair,
    BufferedWriter,
    BytesIO,
    FileIO,
    StringIO,
    TextIOWrapper,
)
from json import JSONDecoder, JSONEncoder
from lzma import LZMACompressor, LZMADecompressor
from multiprocessing import Process
from numbers import Integral
from pathlib import (
    Path,
    PosixPath,
    PurePath,
    PurePosixPath,
    PureWindowsPath,
    WindowsPath,
)
from pickle import Pickler, Unpickler
from struct import Struct
from types import (
    AsyncGeneratorType,
    BuiltinFunctionType,
    BuiltinMethodType,
    CellType,
    ClassMethodDescriptorType,
    CodeType,
    CoroutineType,
    EllipsisType,
    FrameType,
    FunctionType,
    GeneratorType,
    GetSetDescriptorType,
    LambdaType,
    MappingProxyType,
    MemberDescriptorType,
    MethodDescriptorType,
    MethodType,
    MethodWrapperType,
    ModuleType,
    NoneType,
    NotImplementedType,
    TracebackType,
    WrapperDescriptorType,
)
from typing import (
    Annotated,
    Any,
    Dict,
    ForwardRef,
    List,
    Literal,
    NewType,
    Optional,
    ParamSpec,
    Tuple,
    TypeVar,
    Union,
)
from weakref import WeakSet

from sphinx.ext.autodoc._dynamic._mock import mock
from sphinx.util.typing import _INVALID_BUILTIN_CLASSES, restify, stringify_annotation


class MyClass1:
    pass


class MyClass2(MyClass1):
    __qualname__ = '<MyClass2>'


class MyEnum(Enum):
    a = 1


T = TypeVar('T')
MyInt = NewType('MyInt', int)


class MyList(List[T]):
    pass


class BrokenType:
    __args__ = int


@dataclasses.dataclass(frozen=True)
class Gt:
    gt: float


def test_restify() -> None:
    assert restify(int) == ':py:class:`int`'
    assert restify(int, 'smart') == ':py:class:`int`'

    assert restify(str) == ':py:class:`str`'
    assert restify(str, 'smart') == ':py:class:`str`'

    assert restify(None) == ':py:obj:`None`'
    assert restify(None, 'smart') == ':py:obj:`None`'

    assert restify(Integral) == ':py:class:`numbers.Integral`'
    assert restify(Integral, 'smart') == ':py:class:`~numbers.Integral`'

    assert restify(Struct) == ':py:class:`struct.Struct`'
    assert restify(Struct, 'smart') == ':py:class:`~struct.Struct`'

    assert restify(TracebackType) == ':py:class:`types.TracebackType`'
    assert restify(TracebackType, 'smart') == ':py:class:`~types.TracebackType`'

    assert restify(Path) == ':py:class:`pathlib.Path`'
    assert restify(Path, 'smart') == ':py:class:`~pathlib.Path`'

    assert restify(Any) == ':py:obj:`~typing.Any`'
    assert restify(Any, 'smart') == ':py:obj:`~typing.Any`'

    assert restify('str') == 'str'
    assert restify('str', 'smart') == 'str'


def test_is_invalid_builtin_class() -> None:
    # if these tests start failing, it means that the __module__
    # of one of these classes has changed, and _INVALID_BUILTIN_CLASSES
    # in sphinx.util.typing needs to be updated.
    invalid_types = (
        # contextvars
        Context,
        ContextVar,
        Token,
        # ctypes
        ctypes.Array,
        ctypes.Structure,
        ctypes.Union,
        # io
        FileIO,
        BytesIO,
        StringIO,
        BufferedReader,
        BufferedWriter,
        BufferedRWPair,
        BufferedRandom,
        TextIOWrapper,
        # json
        JSONDecoder,
        JSONEncoder,
        # lzma
        LZMACompressor,
        LZMADecompressor,
        # multiprocessing
        Process,
        # pickle
        Pickler,
        Unpickler,
        # struct
        Struct,
        # types
        AsyncGeneratorType,
        BuiltinFunctionType,
        BuiltinMethodType,
        CellType,
        ClassMethodDescriptorType,
        CodeType,
        CoroutineType,
        EllipsisType,
        FrameType,
        FunctionType,
        GeneratorType,
        GetSetDescriptorType,
        LambdaType,
        MappingProxyType,
        MemberDescriptorType,
        MethodDescriptorType,
        MethodType,
        MethodWrapperType,
        ModuleType,
        NoneType,
        NotImplementedType,
        TracebackType,
        WrapperDescriptorType,
        # weakref
        WeakSet,
        # zipfile
        zipfile.Path,
        zipfile.CompleteDirs,
    )
    if sys.version_info[:2] == (3, 13):
        invalid_types += (
            # pathlib
            Path,
            PosixPath,
            PurePath,
            PurePosixPath,
            PureWindowsPath,
            WindowsPath,
        )

    invalid_names = {(cls.__module__, cls.__qualname__) for cls in invalid_types}
    if sys.version_info[:2] != (3, 13):
        invalid_names |= {
            ('pathlib._local', 'Path'),
            ('pathlib._local', 'PosixPath'),
            ('pathlib._local', 'PurePath'),
            ('pathlib._local', 'PurePosixPath'),
            ('pathlib._local', 'PureWindowsPath'),
            ('pathlib._local', 'WindowsPath'),
        }
    assert set(_INVALID_BUILTIN_CLASSES) == invalid_names


def test_restify_type_hints_containers():
    assert restify(List) == ':py:class:`~typing.List`'
    assert restify(Dict) == ':py:class:`~typing.Dict`'
    assert restify(List[int]) == ':py:class:`~typing.List`\\ [:py:class:`int`]'
    assert restify(List[str]) == ':py:class:`~typing.List`\\ [:py:class:`str`]'
    assert restify(Dict[str, float]) == (
        ':py:class:`~typing.Dict`\\ [:py:class:`str`, :py:class:`float`]'
    )
    assert restify(Tuple[str, str, str]) == (
        ':py:class:`~typing.Tuple`\\ '
        '[:py:class:`str`, :py:class:`str`, '
        ':py:class:`str`]'
    )
    ann_rst = restify(Tuple[str, ...])
    assert ann_rst == ':py:class:`~typing.Tuple`\\ [:py:class:`str`, ...]'

    assert restify(Tuple[()]) == ':py:class:`~typing.Tuple`'

    assert restify(List[Dict[str, Tuple]]) == (
        ':py:class:`~typing.List`\\ '
        '[:py:class:`~typing.Dict`\\ '
        '[:py:class:`str`, :py:class:`~typing.Tuple`]]'
    )
    assert restify(MyList[Tuple[int, int]]) == (
        ':py:class:`tests.test_util.test_util_typing.MyList`\\ '
        '[:py:class:`~typing.Tuple`\\ '
        '[:py:class:`int`, :py:class:`int`]]'
    )
    assert restify(t.Generator[None, None, None]) == (
        ':py:class:`~typing.Generator`\\ '
        '[:py:obj:`None`, :py:obj:`None`, '
        ':py:obj:`None`]'
    )
    assert restify(abc.Generator[None, None, None]) == (
        ':py:class:`collections.abc.Generator`\\ '
        '[:py:obj:`None`, :py:obj:`None`, '
        ':py:obj:`None`]'
    )
    assert restify(t.Iterator[None]) == (
        ':py:class:`~typing.Iterator`\\ [:py:obj:`None`]'
    )
    assert restify(abc.Iterator[None]) == (
        ':py:class:`collections.abc.Iterator`\\ [:py:obj:`None`]'
    )


def test_restify_Annotated() -> None:
    ann_rst = restify(Annotated[str, 'foo', 'bar'])
    assert ann_rst == (
        ":py:class:`~typing.Annotated`\\ [:py:class:`str`, 'foo', 'bar']"
    )
    ann_rst = restify(Annotated[str, 'foo', 'bar'], 'smart')
    assert ann_rst == (
        ":py:class:`~typing.Annotated`\\ [:py:class:`str`, 'foo', 'bar']"
    )
    ann_rst = restify(Annotated[float, Gt(-10.0)])
    assert ann_rst == (
        ':py:class:`~typing.Annotated`\\ [:py:class:`float`, :py:class:`tests.test_util.test_util_typing.Gt`\\ (gt=\\ -10.0)]'
    )
    ann_rst = restify(Annotated[float, Gt(-10.0)], 'smart')
    assert ann_rst == (
        ':py:class:`~typing.Annotated`\\ [:py:class:`float`, :py:class:`~tests.test_util.test_util_typing.Gt`\\ (gt=\\ -10.0)]'
    )


def test_restify_type_hints_Callable() -> None:
    assert restify(t.Callable) == ':py:class:`~typing.Callable`'
    assert restify(t.Callable[[str], int]) == (
        ':py:class:`~typing.Callable`\\ [[:py:class:`str`], :py:class:`int`]'
    )
    assert restify(t.Callable[..., int]) == (
        ':py:class:`~typing.Callable`\\ [[...], :py:class:`int`]'
    )
    assert restify(abc.Callable) == ':py:class:`collections.abc.Callable`'
    assert restify(abc.Callable[[str], int]) == (
        ':py:class:`collections.abc.Callable`\\ [[:py:class:`str`], :py:class:`int`]'
    )
    assert restify(abc.Callable[..., int]) == (
        ':py:class:`collections.abc.Callable`\\ [[...], :py:class:`int`]'
    )


def test_restify_type_hints_Union() -> None:
    assert restify(Union[int]) == ':py:class:`int`'
    assert restify(Union[int, str]) == ':py:class:`int` | :py:class:`str`'
    assert restify(Optional[int]) == ':py:class:`int` | :py:obj:`None`'

    assert restify(Union[str, None]) == ':py:class:`str` | :py:obj:`None`'
    assert restify(Union[None, str]) == ':py:obj:`None` | :py:class:`str`'
    assert restify(Optional[str]) == ':py:class:`str` | :py:obj:`None`'

    assert restify(Union[int, str, None]) == (
        ':py:class:`int` | :py:class:`str` | :py:obj:`None`'
    )
    assert restify(Optional[Union[int, str]]) in {
        ':py:class:`str` | :py:class:`int` | :py:obj:`None`',
        ':py:class:`int` | :py:class:`str` | :py:obj:`None`',
    }

    assert restify(Union[int, Integral]) == (
        ':py:class:`int` | :py:class:`numbers.Integral`'
    )
    assert restify(Union[int, Integral], 'smart') == (
        ':py:class:`int` | :py:class:`~numbers.Integral`'
    )

    assert restify(Union[MyClass1, MyClass2]) == (
        ':py:class:`tests.test_util.test_util_typing.MyClass1`'
        ' | :py:class:`tests.test_util.test_util_typing.<MyClass2>`'
    )
    assert restify(Union[MyClass1, MyClass2], 'smart') == (
        ':py:class:`~tests.test_util.test_util_typing.MyClass1`'
        ' | :py:class:`~tests.test_util.test_util_typing.<MyClass2>`'
    )

    assert restify(Optional[Union[MyClass1, MyClass2]]) == (
        ':py:class:`tests.test_util.test_util_typing.MyClass1`'
        ' | :py:class:`tests.test_util.test_util_typing.<MyClass2>`'
        ' | :py:obj:`None`'
    )
    assert restify(Optional[Union[MyClass1, MyClass2]], 'smart') == (
        ':py:class:`~tests.test_util.test_util_typing.MyClass1`'
        ' | :py:class:`~tests.test_util.test_util_typing.<MyClass2>`'
        ' | :py:obj:`None`'
    )


def test_restify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    assert restify(T) == ':py:obj:`tests.test_util.test_util_typing.T`'
    assert restify(T, 'smart') == ':py:obj:`~tests.test_util.test_util_typing.T`'

    assert restify(T_co) == ':py:obj:`tests.test_util.test_util_typing.T_co`'
    assert restify(T_co, 'smart') == ':py:obj:`~tests.test_util.test_util_typing.T_co`'

    assert restify(T_contra) == ':py:obj:`tests.test_util.test_util_typing.T_contra`'
    ann_rst = restify(T_contra, 'smart')
    assert ann_rst == ':py:obj:`~tests.test_util.test_util_typing.T_contra`'

    ann_rst = restify(List[T])
    assert ann_rst == (
        ':py:class:`~typing.List`\\ [:py:obj:`tests.test_util.test_util_typing.T`]'
    )
    ann_rst = restify(List[T], 'smart')
    assert ann_rst == (
        ':py:class:`~typing.List`\\ [:py:obj:`~tests.test_util.test_util_typing.T`]'
    )

    ann_rst = restify(list[T])
    assert ann_rst == (
        ':py:class:`list`\\ [:py:obj:`tests.test_util.test_util_typing.T`]'
    )
    ann_rst = restify(list[T], 'smart')
    assert ann_rst == (
        ':py:class:`list`\\ [:py:obj:`~tests.test_util.test_util_typing.T`]'
    )

    assert restify(MyInt) == ':py:class:`tests.test_util.test_util_typing.MyInt`'
    ann_rst = restify(MyInt, 'smart')
    assert ann_rst == ':py:class:`~tests.test_util.test_util_typing.MyInt`'


def test_restify_type_hints_custom_class() -> None:
    assert restify(MyClass1) == ':py:class:`tests.test_util.test_util_typing.MyClass1`'
    ann_rst = restify(MyClass1, 'smart')
    assert ann_rst == ':py:class:`~tests.test_util.test_util_typing.MyClass1`'

    ann_rst = restify(MyClass2)
    assert ann_rst == ':py:class:`tests.test_util.test_util_typing.<MyClass2>`'
    ann_rst = restify(MyClass2, 'smart')
    assert ann_rst == ':py:class:`~tests.test_util.test_util_typing.<MyClass2>`'


def test_restify_type_hints_alias() -> None:
    MyStr = str
    MyTypingTuple = Tuple[str, str]
    MyTuple = tuple[str, str]
    assert restify(MyStr) == ':py:class:`str`'
    ann_rst = restify(MyTypingTuple)
    assert ann_rst == ':py:class:`~typing.Tuple`\\ [:py:class:`str`, :py:class:`str`]'
    assert restify(MyTuple) == ':py:class:`tuple`\\ [:py:class:`str`, :py:class:`str`]'


def test_restify_type_ForwardRef():
    assert restify(ForwardRef('MyInt')) == ':py:class:`MyInt`'

    assert (
        restify(list[ForwardRef('MyInt')]) == ':py:class:`list`\\ [:py:class:`MyInt`]'  # ty: ignore[invalid-type-form]
    )

    ann_rst = restify(Tuple[dict[ForwardRef('MyInt'), str], list[List[int]]])  # ty: ignore[invalid-type-form]
    assert ann_rst == (
        ':py:class:`~typing.Tuple`\\ [:py:class:`dict`\\ [:py:class:`MyInt`, :py:class:`str`], :py:class:`list`\\ [:py:class:`~typing.List`\\ [:py:class:`int`]]]'
    )


def test_restify_type_Literal() -> None:
    ann_rst = restify(Literal[1, '2', '\r'])
    assert ann_rst == ":py:obj:`~typing.Literal`\\ [1, '2', '\\r']"

    ann_rst = restify(Literal[MyEnum.a], 'fully-qualified-except-typing')
    assert ann_rst == (
        ':py:obj:`~typing.Literal`\\ [:py:attr:`tests.test_util.test_util_typing.MyEnum.a`]'
    )
    ann_rst = restify(Literal[MyEnum.a], 'smart')
    assert ann_rst == (
        ':py:obj:`~typing.Literal`\\ [:py:attr:`~tests.test_util.test_util_typing.MyEnum.a`]'
    )


def test_restify_pep_585() -> None:
    assert restify(list[str]) == ':py:class:`list`\\ [:py:class:`str`]'
    ann_rst = restify(dict[str, str])
    assert ann_rst == ':py:class:`dict`\\ [:py:class:`str`, :py:class:`str`]'
    assert restify(tuple[str, ...]) == ':py:class:`tuple`\\ [:py:class:`str`, ...]'
    assert restify(tuple[str, str, str]) == (
        ':py:class:`tuple`\\ [:py:class:`str`, :py:class:`str`, :py:class:`str`]'
    )
    ann_rst = restify(dict[str, tuple[int, ...]])
    assert ann_rst == (
        ':py:class:`dict`\\ '
        '[:py:class:`str`, :py:class:`tuple`\\ '
        '[:py:class:`int`, ...]]'
    )

    assert restify(tuple[()]) == ':py:class:`tuple`\\ [()]'

    # Mix old typing with PEP 585
    assert restify(List[dict[str, Tuple[str, ...]]]) == (
        ':py:class:`~typing.List`\\ '
        '[:py:class:`dict`\\ '
        '[:py:class:`str`, :py:class:`~typing.Tuple`\\ '
        '[:py:class:`str`, ...]]]'
    )
    assert restify(tuple[MyList[list[int]], int]) == (
        ':py:class:`tuple`\\ ['
        ':py:class:`tests.test_util.test_util_typing.MyList`\\ '
        '[:py:class:`list`\\ [:py:class:`int`]], '
        ':py:class:`int`]'
    )


def test_restify_Unpack() -> None:
    from typing_extensions import Unpack as UnpackCompat

    class X(t.TypedDict):
        x: int
        y: int
        label: str

    # Unpack is considered as typing special form so we always have '~'
    expect = r':py:obj:`~typing.Unpack`\ [:py:class:`X`]'
    assert restify(UnpackCompat['X'], 'fully-qualified-except-typing') == expect
    assert restify(UnpackCompat['X'], 'smart') == expect

    expect = r':py:obj:`~typing.Unpack`\ [:py:class:`X`]'
    assert restify(t.Unpack['X'], 'fully-qualified-except-typing') == expect
    assert restify(t.Unpack['X'], 'smart') == expect


def test_restify_type_union_operator() -> None:
    assert restify(int | None) == ':py:class:`int` | :py:obj:`None`'
    assert restify(None | int) == ':py:obj:`None` | :py:class:`int`'
    assert restify(int | str) == ':py:class:`int` | :py:class:`str`'
    ann_rst = restify(int | str | None)
    assert ann_rst == ':py:class:`int` | :py:class:`str` | :py:obj:`None`'


def test_restify_broken_type_hints() -> None:
    ann_rst = restify(BrokenType)
    assert ann_rst == ':py:class:`tests.test_util.test_util_typing.BrokenType`'
    ann_rst = restify(BrokenType, 'smart')
    assert ann_rst == ':py:class:`~tests.test_util.test_util_typing.BrokenType`'


def test_restify_mock() -> None:
    with mock(['unknown']):
        import unknown  # type: ignore[import-not-found]

        assert restify(unknown) == ':py:class:`unknown`'
        assert restify(unknown.secret.Class) == ':py:class:`unknown.secret.Class`'
        ann_rst = restify(unknown.secret.Class, 'smart')
        assert ann_rst == ':py:class:`~unknown.secret.Class`'


def test_restify_type_hints_paramspec():
    P = ParamSpec('P')

    assert restify(P) == ':py:obj:`tests.test_util.test_util_typing.P`'
    assert restify(P, 'smart') == ':py:obj:`~tests.test_util.test_util_typing.P`'

    assert restify(P.args) == 'P.args'
    assert restify(P.args, 'smart') == 'P.args'

    assert restify(P.kwargs) == 'P.kwargs'
    assert restify(P.kwargs, 'smart') == 'P.kwargs'


def test_stringify_annotation() -> None:
    assert stringify_annotation(int, 'fully-qualified-except-typing') == 'int'
    assert stringify_annotation(int, 'smart') == 'int'

    assert stringify_annotation(str, 'fully-qualified-except-typing') == 'str'
    assert stringify_annotation(str, 'smart') == 'str'

    assert stringify_annotation(None, 'fully-qualified-except-typing') == 'None'
    assert stringify_annotation(None, 'smart') == 'None'

    ann_str = stringify_annotation(Integral, 'fully-qualified-except-typing')
    assert ann_str == 'numbers.Integral'
    assert stringify_annotation(Integral, 'smart') == '~numbers.Integral'

    ann_str = stringify_annotation(Struct, 'fully-qualified-except-typing')
    assert ann_str == 'struct.Struct'
    assert stringify_annotation(Struct, 'smart') == '~struct.Struct'

    ann_str = stringify_annotation(TracebackType, 'fully-qualified-except-typing')
    assert ann_str == 'types.TracebackType'
    assert stringify_annotation(TracebackType, 'smart') == '~types.TracebackType'

    ann_str = stringify_annotation(Path, 'fully-qualified-except-typing')
    assert ann_str == 'pathlib.Path'
    assert stringify_annotation(Path, 'smart') == '~pathlib.Path'

    assert stringify_annotation(Any, 'fully-qualified-except-typing') == 'Any'
    assert stringify_annotation(Any, 'fully-qualified') == 'typing.Any'
    assert stringify_annotation(Any, 'smart') == '~typing.Any'


def test_stringify_type_hints_containers():
    assert stringify_annotation(List, 'fully-qualified-except-typing') == 'List'
    assert stringify_annotation(List, 'fully-qualified') == 'typing.List'
    assert stringify_annotation(List, 'smart') == '~typing.List'

    assert stringify_annotation(Dict, 'fully-qualified-except-typing') == 'Dict'
    assert stringify_annotation(Dict, 'fully-qualified') == 'typing.Dict'
    assert stringify_annotation(Dict, 'smart') == '~typing.Dict'

    ann_str = stringify_annotation(List[int], 'fully-qualified-except-typing')
    assert ann_str == 'List[int]'
    assert stringify_annotation(List[int], 'fully-qualified') == 'typing.List[int]'
    assert stringify_annotation(List[int], 'smart') == '~typing.List[int]'

    ann_str = stringify_annotation(List[str], 'fully-qualified-except-typing')
    assert ann_str == 'List[str]'
    assert stringify_annotation(List[str], 'fully-qualified') == 'typing.List[str]'
    assert stringify_annotation(List[str], 'smart') == '~typing.List[str]'

    ann_str = stringify_annotation(Dict[str, float], 'fully-qualified-except-typing')
    assert ann_str == 'Dict[str, float]'
    ann_str = stringify_annotation(Dict[str, float], 'fully-qualified')
    assert ann_str == 'typing.Dict[str, float]'
    assert stringify_annotation(Dict[str, float], 'smart') == '~typing.Dict[str, float]'

    ann_str = stringify_annotation(
        Tuple[str, str, str], 'fully-qualified-except-typing'
    )
    assert ann_str == 'Tuple[str, str, str]'
    ann_str = stringify_annotation(Tuple[str, str, str], 'fully-qualified')
    assert ann_str == 'typing.Tuple[str, str, str]'
    ann_str = stringify_annotation(Tuple[str, str, str], 'smart')
    assert ann_str == '~typing.Tuple[str, str, str]'

    ann_str = stringify_annotation(Tuple[str, ...], 'fully-qualified-except-typing')
    assert ann_str == 'Tuple[str, ...]'
    ann_str = stringify_annotation(Tuple[str, ...], 'fully-qualified')
    assert ann_str == 'typing.Tuple[str, ...]'
    assert stringify_annotation(Tuple[str, ...], 'smart') == '~typing.Tuple[str, ...]'

    assert stringify_annotation(Tuple[()], 'fully-qualified-except-typing') == 'Tuple'
    assert stringify_annotation(Tuple[()], 'fully-qualified') == 'typing.Tuple'
    assert stringify_annotation(Tuple[()], 'smart') == '~typing.Tuple'

    ann_str = stringify_annotation(
        List[Dict[str, Tuple]], 'fully-qualified-except-typing'
    )
    assert ann_str == 'List[Dict[str, Tuple]]'
    ann_str = stringify_annotation(List[Dict[str, Tuple]], 'fully-qualified')
    assert ann_str == 'typing.List[typing.Dict[str, typing.Tuple]]'
    ann_str = stringify_annotation(List[Dict[str, Tuple]], 'smart')
    assert ann_str == '~typing.List[~typing.Dict[str, ~typing.Tuple]]'

    ann_str = stringify_annotation(
        MyList[Tuple[int, int]], 'fully-qualified-except-typing'
    )
    assert ann_str == 'tests.test_util.test_util_typing.MyList[Tuple[int, int]]'
    ann_str = stringify_annotation(MyList[Tuple[int, int]], 'fully-qualified')
    assert ann_str == (
        'tests.test_util.test_util_typing.MyList[typing.Tuple[int, int]]'
    )
    ann_str = stringify_annotation(MyList[Tuple[int, int]], 'smart')
    assert ann_str == (
        '~tests.test_util.test_util_typing.MyList[~typing.Tuple[int, int]]'
    )

    ann_str = stringify_annotation(
        t.Generator[None, None, None], 'fully-qualified-except-typing'
    )
    assert ann_str == 'Generator[None, None, None]'
    ann_str = stringify_annotation(t.Generator[None, None, None], 'fully-qualified')
    assert ann_str == 'typing.Generator[None, None, None]'
    ann_str = stringify_annotation(t.Generator[None, None, None], 'smart')
    assert ann_str == '~typing.Generator[None, None, None]'

    ann_str = stringify_annotation(
        abc.Generator[None, None, None], 'fully-qualified-except-typing'
    )
    assert ann_str == 'collections.abc.Generator[None, None, None]'
    ann_str = stringify_annotation(abc.Generator[None, None, None], 'fully-qualified')
    assert ann_str == 'collections.abc.Generator[None, None, None]'
    ann_str = stringify_annotation(abc.Generator[None, None, None], 'smart')
    assert ann_str == '~collections.abc.Generator[None, None, None]'

    ann_str = stringify_annotation(t.Iterator[None], 'fully-qualified-except-typing')
    assert ann_str == 'Iterator[None]'
    ann_str = stringify_annotation(t.Iterator[None], 'fully-qualified')
    assert ann_str == 'typing.Iterator[None]'
    assert stringify_annotation(t.Iterator[None], 'smart') == '~typing.Iterator[None]'

    ann_str = stringify_annotation(abc.Iterator[None], 'fully-qualified-except-typing')
    assert ann_str == 'collections.abc.Iterator[None]'
    ann_str = stringify_annotation(abc.Iterator[None], 'fully-qualified')
    assert ann_str == 'collections.abc.Iterator[None]'
    ann_str = stringify_annotation(abc.Iterator[None], 'smart')
    assert ann_str == '~collections.abc.Iterator[None]'


def test_stringify_type_hints_pep_585():
    ann_str = stringify_annotation(list[int], 'fully-qualified-except-typing')
    assert ann_str == 'list[int]'
    assert stringify_annotation(list[int], 'smart') == 'list[int]'

    ann_str = stringify_annotation(list[str], 'fully-qualified-except-typing')
    assert ann_str == 'list[str]'
    assert stringify_annotation(list[str], 'smart') == 'list[str]'

    ann_str = stringify_annotation(dict[str, float], 'fully-qualified-except-typing')
    assert ann_str == 'dict[str, float]'
    assert stringify_annotation(dict[str, float], 'smart') == 'dict[str, float]'

    ann_str = stringify_annotation(
        tuple[str, str, str], 'fully-qualified-except-typing'
    )
    assert ann_str == 'tuple[str, str, str]'
    assert stringify_annotation(tuple[str, str, str], 'smart') == 'tuple[str, str, str]'

    ann_str = stringify_annotation(tuple[str, ...], 'fully-qualified-except-typing')
    assert ann_str == 'tuple[str, ...]'
    assert stringify_annotation(tuple[str, ...], 'smart') == 'tuple[str, ...]'

    assert (
        stringify_annotation(tuple[()], 'fully-qualified-except-typing') == 'tuple[()]'
    )
    assert stringify_annotation(tuple[()], 'smart') == 'tuple[()]'

    ann_str = stringify_annotation(
        list[dict[str, tuple]], 'fully-qualified-except-typing'
    )
    assert ann_str == 'list[dict[str, tuple]]'
    ann_str = stringify_annotation(list[dict[str, tuple]], 'smart')
    assert ann_str == 'list[dict[str, tuple]]'

    ann_str = stringify_annotation(
        MyList[tuple[int, int]], 'fully-qualified-except-typing'
    )
    assert ann_str == 'tests.test_util.test_util_typing.MyList[tuple[int, int]]'
    ann_str = stringify_annotation(MyList[tuple[int, int]], 'fully-qualified')
    assert ann_str == 'tests.test_util.test_util_typing.MyList[tuple[int, int]]'
    ann_str = stringify_annotation(MyList[tuple[int, int]], 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.MyList[tuple[int, int]]'

    ann_str = stringify_annotation(type[int], 'fully-qualified-except-typing')
    assert ann_str == 'type[int]'
    assert stringify_annotation(type[int], 'smart') == 'type[int]'

    # Mix typing and pep 585
    ann_str = stringify_annotation(
        tuple[List[dict[int, str]], str, ...], 'fully-qualified-except-typing'
    )
    assert ann_str == 'tuple[List[dict[int, str]], str, ...]'
    ann_str = stringify_annotation(tuple[List[dict[int, str]], str, ...], 'smart')
    assert ann_str == 'tuple[~typing.List[dict[int, str]], str, ...]'


def test_stringify_Annotated() -> None:
    ann_str = stringify_annotation(
        Annotated[str, 'foo', 'bar'], 'fully-qualified-except-typing'
    )
    assert ann_str == "Annotated[str, 'foo', 'bar']"
    ann_str = stringify_annotation(Annotated[str, 'foo', 'bar'], 'smart')
    assert ann_str == "~typing.Annotated[str, 'foo', 'bar']"
    ann_str = stringify_annotation(
        Annotated[float, Gt(-10.0)], 'fully-qualified-except-typing'
    )
    assert ann_str == (
        'Annotated[float, tests.test_util.test_util_typing.Gt(gt=-10.0)]'
    )
    ann_str = stringify_annotation(Annotated[float, Gt(-10.0)], 'smart')
    assert ann_str == (
        '~typing.Annotated[float, ~tests.test_util.test_util_typing.Gt(gt=-10.0)]'
    )


def test_stringify_Unpack() -> None:
    class X(t.TypedDict):
        x: int
        y: int
        label: str

    assert stringify_annotation(t.Unpack['X']) == 'Unpack[X]'
    assert stringify_annotation(t.Unpack['X'], 'smart') == '~typing.Unpack[X]'


def test_stringify_type_hints_string() -> None:
    assert stringify_annotation('int', 'fully-qualified-except-typing') == 'int'
    assert stringify_annotation('int', 'fully-qualified') == 'int'
    assert stringify_annotation('int', 'smart') == 'int'

    assert stringify_annotation('str', 'fully-qualified-except-typing') == 'str'
    assert stringify_annotation('str', 'fully-qualified') == 'str'
    assert stringify_annotation('str', 'smart') == 'str'

    ann_str = stringify_annotation(List['int'], 'fully-qualified-except-typing')
    assert ann_str == 'List[int]'
    assert stringify_annotation(List['int'], 'fully-qualified') == 'typing.List[int]'
    assert stringify_annotation(List['int'], 'smart') == '~typing.List[int]'

    ann_str = stringify_annotation(list['int'], 'fully-qualified-except-typing')
    assert ann_str == 'list[int]'
    assert stringify_annotation(list['int'], 'fully-qualified') == 'list[int]'
    assert stringify_annotation(list['int'], 'smart') == 'list[int]'

    ann_str = stringify_annotation('Tuple[str]', 'fully-qualified-except-typing')
    assert ann_str == 'Tuple[str]'
    assert stringify_annotation('Tuple[str]', 'fully-qualified') == 'Tuple[str]'
    assert stringify_annotation('Tuple[str]', 'smart') == 'Tuple[str]'

    ann_str = stringify_annotation('tuple[str]', 'fully-qualified-except-typing')
    assert ann_str == 'tuple[str]'
    assert stringify_annotation('tuple[str]', 'fully-qualified') == 'tuple[str]'
    assert stringify_annotation('tuple[str]', 'smart') == 'tuple[str]'

    assert stringify_annotation('unknown', 'fully-qualified-except-typing') == 'unknown'
    assert stringify_annotation('unknown', 'fully-qualified') == 'unknown'
    assert stringify_annotation('unknown', 'smart') == 'unknown'


def test_stringify_type_hints_Callable() -> None:
    ann_str = stringify_annotation(t.Callable, 'fully-qualified-except-typing')
    assert ann_str == 'Callable'
    assert stringify_annotation(t.Callable, 'fully-qualified') == 'typing.Callable'
    assert stringify_annotation(t.Callable, 'smart') == '~typing.Callable'

    ann_str = stringify_annotation(
        t.Callable[[str], int], 'fully-qualified-except-typing'
    )
    assert ann_str == 'Callable[[str], int]'
    ann_str = stringify_annotation(t.Callable[[str], int], 'fully-qualified')
    assert ann_str == 'typing.Callable[[str], int]'
    ann_str = stringify_annotation(t.Callable[[str], int], 'smart')
    assert ann_str == '~typing.Callable[[str], int]'

    ann_str = stringify_annotation(
        t.Callable[..., int], 'fully-qualified-except-typing'
    )
    assert ann_str == 'Callable[[...], int]'
    ann_str = stringify_annotation(t.Callable[..., int], 'fully-qualified')
    assert ann_str == 'typing.Callable[[...], int]'
    ann_str = stringify_annotation(t.Callable[..., int], 'smart')
    assert ann_str == '~typing.Callable[[...], int]'

    ann_str = stringify_annotation(abc.Callable, 'fully-qualified-except-typing')
    assert ann_str == 'collections.abc.Callable'
    ann_str = stringify_annotation(abc.Callable, 'fully-qualified')
    assert ann_str == 'collections.abc.Callable'
    assert stringify_annotation(abc.Callable, 'smart') == '~collections.abc.Callable'

    ann_str = stringify_annotation(
        abc.Callable[[str], int], 'fully-qualified-except-typing'
    )
    assert ann_str == 'collections.abc.Callable[[str], int]'
    ann_str = stringify_annotation(abc.Callable[[str], int], 'fully-qualified')
    assert ann_str == 'collections.abc.Callable[[str], int]'
    ann_str = stringify_annotation(abc.Callable[[str], int], 'smart')
    assert ann_str == '~collections.abc.Callable[[str], int]'

    ann_str = stringify_annotation(
        abc.Callable[..., int], 'fully-qualified-except-typing'
    )
    assert ann_str == 'collections.abc.Callable[[...], int]'
    ann_str = stringify_annotation(abc.Callable[..., int], 'fully-qualified')
    assert ann_str == 'collections.abc.Callable[[...], int]'
    ann_str = stringify_annotation(abc.Callable[..., int], 'smart')
    assert ann_str == '~collections.abc.Callable[[...], int]'


def test_stringify_type_hints_Union() -> None:
    ann_str = stringify_annotation(Optional[int], 'fully-qualified-except-typing')
    assert ann_str == 'int | None'
    assert stringify_annotation(Optional[int], 'fully-qualified') == 'int | None'
    assert stringify_annotation(Optional[int], 'smart') == 'int | None'

    ann_str = stringify_annotation(Union[int, None], 'fully-qualified-except-typing')
    assert ann_str == 'int | None'
    ann_str = stringify_annotation(Union[None, int], 'fully-qualified-except-typing')
    assert ann_str == 'None | int'
    assert stringify_annotation(Union[int, None], 'fully-qualified') == 'int | None'
    assert stringify_annotation(Union[None, int], 'fully-qualified') == 'None | int'
    assert stringify_annotation(Union[int, None], 'smart') == 'int | None'
    assert stringify_annotation(Union[None, int], 'smart') == 'None | int'

    ann_str = stringify_annotation(Union[int, str], 'fully-qualified-except-typing')
    assert ann_str == 'int | str'
    assert stringify_annotation(Union[int, str], 'fully-qualified') == 'int | str'
    assert stringify_annotation(Union[int, str], 'smart') == 'int | str'

    ann_str = stringify_annotation(
        Union[int, Integral], 'fully-qualified-except-typing'
    )
    assert ann_str == 'int | numbers.Integral'
    ann_str = stringify_annotation(Union[int, Integral], 'fully-qualified')
    assert ann_str == 'int | numbers.Integral'
    ann_str = stringify_annotation(Union[int, Integral], 'smart')
    assert ann_str == 'int | ~numbers.Integral'

    ann_str = stringify_annotation(
        Union[MyClass1, MyClass2], 'fully-qualified-except-typing'
    )
    assert ann_str == (
        'tests.test_util.test_util_typing.MyClass1 | tests.test_util.test_util_typing.<MyClass2>'
    )
    ann_str = stringify_annotation(Union[MyClass1, MyClass2], 'fully-qualified')
    assert ann_str == (
        'tests.test_util.test_util_typing.MyClass1 | tests.test_util.test_util_typing.<MyClass2>'
    )
    ann_str = stringify_annotation(Union[MyClass1, MyClass2], 'smart')
    assert ann_str == (
        '~tests.test_util.test_util_typing.MyClass1 | ~tests.test_util.test_util_typing.<MyClass2>'
    )


def test_stringify_type_hints_typevars():
    T = TypeVar('T')
    T_co = TypeVar('T_co', covariant=True)
    T_contra = TypeVar('T_contra', contravariant=True)

    ann_str = stringify_annotation(T, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.T'
    assert stringify_annotation(T, 'smart') == '~tests.test_util.test_util_typing.T'

    ann_str = stringify_annotation(T_co, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.T_co'
    ann_str = stringify_annotation(T_co, 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.T_co'

    ann_str = stringify_annotation(T_contra, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.T_contra'
    ann_str = stringify_annotation(T_contra, 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.T_contra'

    ann_str = stringify_annotation(List[T], 'fully-qualified-except-typing')
    assert ann_str == 'List[tests.test_util.test_util_typing.T]'
    ann_str = stringify_annotation(List[T], 'smart')
    assert ann_str == '~typing.List[~tests.test_util.test_util_typing.T]'

    ann_str = stringify_annotation(list[T], 'fully-qualified-except-typing')
    assert ann_str == 'list[tests.test_util.test_util_typing.T]'
    ann_str = stringify_annotation(list[T], 'smart')
    assert ann_str == 'list[~tests.test_util.test_util_typing.T]'

    ann_str = stringify_annotation(MyInt, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.MyInt'
    ann_str = stringify_annotation(MyInt, 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.MyInt'


def test_stringify_type_hints_custom_class() -> None:
    ann_str = stringify_annotation(MyClass1, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.MyClass1'
    ann_str = stringify_annotation(MyClass1, 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.MyClass1'

    ann_str = stringify_annotation(MyClass2, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.<MyClass2>'
    ann_str = stringify_annotation(MyClass2, 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.<MyClass2>'


def test_stringify_type_hints_alias() -> None:
    MyStr = str
    MyTuple = Tuple[str, str]

    assert stringify_annotation(MyStr, 'fully-qualified-except-typing') == 'str'
    assert stringify_annotation(MyStr, 'smart') == 'str'

    assert stringify_annotation(MyTuple) == 'Tuple[str, str]'
    assert stringify_annotation(MyTuple, 'smart') == '~typing.Tuple[str, str]'


def test_stringify_type_Literal() -> None:
    ann_str = stringify_annotation(
        Literal[1, '2', '\r'], 'fully-qualified-except-typing'
    )
    assert ann_str == "Literal[1, '2', '\\r']"
    ann_str = stringify_annotation(Literal[1, '2', '\r'], 'fully-qualified')
    assert ann_str == "typing.Literal[1, '2', '\\r']"
    ann_str = stringify_annotation(Literal[1, '2', '\r'], 'smart')
    assert ann_str == "~typing.Literal[1, '2', '\\r']"

    ann_str = stringify_annotation(Literal[MyEnum.a], 'fully-qualified-except-typing')
    assert ann_str == 'Literal[tests.test_util.test_util_typing.MyEnum.a]'
    ann_str = stringify_annotation(Literal[MyEnum.a], 'fully-qualified')
    assert ann_str == 'typing.Literal[tests.test_util.test_util_typing.MyEnum.a]'
    ann_str = stringify_annotation(Literal[MyEnum.a], 'smart')
    assert ann_str == '~typing.Literal[MyEnum.a]'


def test_stringify_type_union_operator() -> None:
    assert stringify_annotation(int | None) == 'int | None'
    assert stringify_annotation(int | None, 'smart') == 'int | None'

    assert stringify_annotation(int | str) == 'int | str'
    assert stringify_annotation(int | str, 'smart') == 'int | str'

    assert stringify_annotation(int | str | None) == 'int | str | None'
    assert stringify_annotation(int | str | None, 'smart') == 'int | str | None'

    ann_str = stringify_annotation(
        int | tuple[dict[str, int | None], list[int | str]] | None
    )
    assert ann_str == 'int | tuple[dict[str, int | None], list[int | str]] | None'
    ann_str = stringify_annotation(
        int | tuple[dict[str, int | None], list[int | str]] | None, 'smart'
    )
    assert ann_str == 'int | tuple[dict[str, int | None], list[int | str]] | None'

    assert stringify_annotation(int | Struct) == 'int | struct.Struct'
    assert stringify_annotation(int | Struct, 'smart') == 'int | ~struct.Struct'


def test_stringify_broken_type_hints() -> None:
    ann_str = stringify_annotation(BrokenType, 'fully-qualified-except-typing')
    assert ann_str == 'tests.test_util.test_util_typing.BrokenType'
    ann_str = stringify_annotation(BrokenType, 'smart')
    assert ann_str == '~tests.test_util.test_util_typing.BrokenType'


def test_stringify_mock() -> None:
    with mock(['unknown']):
        import unknown  # ty: ignore[unresolved-import]

        ann_str = stringify_annotation(unknown, 'fully-qualified-except-typing')
        assert ann_str == 'unknown'
        ann_str = stringify_annotation(
            unknown.secret.Class, 'fully-qualified-except-typing'
        )
        assert ann_str == 'unknown.secret.Class'
        ann_str = stringify_annotation(unknown.secret.Class, 'smart')
        assert ann_str == 'unknown.secret.Class'


def test_stringify_type_ForwardRef():
    assert stringify_annotation(ForwardRef('MyInt')) == 'MyInt'
    assert stringify_annotation(ForwardRef('MyInt'), 'smart') == 'MyInt'

    assert stringify_annotation(list[ForwardRef('MyInt')]) == 'list[MyInt]'  # ty: ignore[invalid-type-form]
    assert stringify_annotation(list[ForwardRef('MyInt')], 'smart') == 'list[MyInt]'  # ty: ignore[invalid-type-form]

    ann_str = stringify_annotation(
        Tuple[dict[ForwardRef('MyInt'), str], list[List[int]]]  # ty: ignore[invalid-type-form]
    )
    assert ann_str == 'Tuple[dict[MyInt, str], list[List[int]]]'
    ann_str = stringify_annotation(
        Tuple[dict[ForwardRef('MyInt'), str], list[List[int]]],  # ty: ignore[invalid-type-form]
        'fully-qualified-except-typing',
    )
    assert ann_str == 'Tuple[dict[MyInt, str], list[List[int]]]'
    ann_str = stringify_annotation(
        Tuple[dict[ForwardRef('MyInt'), str], list[List[int]]],  # ty: ignore[invalid-type-form]
        'smart',
    )
    assert ann_str == '~typing.Tuple[dict[MyInt, str], list[~typing.List[int]]]'


def test_stringify_type_hints_paramspec():
    P = ParamSpec('P')

    assert stringify_annotation(P, 'fully-qualified') == '~P'
    assert stringify_annotation(P, 'fully-qualified-except-typing') == '~P'
    assert stringify_annotation(P, 'smart') == '~P'

    assert stringify_annotation(P.args, 'fully-qualified') == 'typing.~P'
    assert stringify_annotation(P.args, 'fully-qualified-except-typing') == '~P'
    assert stringify_annotation(P.args, 'smart') == '~typing.~P'

    assert stringify_annotation(P.kwargs, 'fully-qualified') == 'typing.~P'
    assert stringify_annotation(P.kwargs, 'fully-qualified-except-typing') == '~P'
    assert stringify_annotation(P.kwargs, 'smart') == '~typing.~P'
