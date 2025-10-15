"""Module to test type alias cross-reference resolution."""

from __future__ import annotations

import pathlib

import typing_extensions

#: Any type of path
pathlike = str | pathlib.Path

#: A generic type alias for error handlers
Handler = type[Exception]

#: A PEP 695 type alias for error handlers
HandlerType = typing_extensions.TypeAliasType('HandlerType', type[Exception])


def read_file(path: pathlike) -> bytes:
    """Read a file and return its contents.

    Tests Union type alias cross-reference resolution.
    """
    with open(path, 'rb') as f:
        return f.read()


def process_error(handler: Handler, other: HandlerType) -> str:
    """Process an error with a custom handler type.

    Tests generic type alias cross-reference resolution.
    """
    return f'Handled by {handler.__name__}'
