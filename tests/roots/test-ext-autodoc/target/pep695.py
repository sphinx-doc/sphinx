from __future__ import annotations

import pathlib
from typing import NewType, TypeAliasType

import typing_extensions

#: Some buffer-like object
buffer_like = bytes | bytearray | memoryview

#: Any type of path
pathlike = str | pathlib.Path

#: A generic type alias
Handler = type[Exception]


class Foo:
    """This is class Foo."""


type Pep695Alias = Foo
"""This is PEP695 type alias."""

type Pep695AliasUndocumented = Foo

TypeAliasTypeExplicit = TypeAliasType('TypeAliasTypeExplicit', Foo)  # NoQA: UP040
"""This is an explicitly constructed typing.TypeAlias."""

HandlerTypeAliasType = TypeAliasType('HandlerTypeAliasType', type[Exception])  # NoQA: UP040
"""This is an explicitly constructed generic alias typing.TypeAlias."""

TypeAliasTypeExtension = typing_extensions.TypeAliasType('TypeAliasTypeExtension', Foo)  # NoQA: UP040
"""This is an explicitly constructed typing_extensions.TypeAlias."""

#: This is PEP695 complex type alias with doc comment.
type Pep695AliasC = dict[str, Foo]

type Pep695AliasUnion = str | int
"""This is PEP695 type alias for union."""

type Pep695AliasOfAlias = Pep695AliasC
"""This is PEP695 type alias of PEP695 alias."""

Bar = NewType('Bar', Pep695Alias)
"""This is newtype of Pep695Alias."""


def ret_pep695(a: Pep695Alias) -> Pep695Alias:
    """This fn accepts and returns PEP695 alias."""
    ...


def read_file(path: pathlike) -> bytes:
    """Read a file and return its contents.

    Tests Union type alias cross-reference resolution.
    """


def process_error(handler: Handler, other: HandlerTypeAliasType) -> str:
    """Process an error with a custom handler type.

    Tests generic type alias cross-reference resolution.
    """


def buffer_len(data: buffer_like) -> int:
    """Return length of a buffer-like object.

    Tests Union type alias cross-reference resolution.
    """
