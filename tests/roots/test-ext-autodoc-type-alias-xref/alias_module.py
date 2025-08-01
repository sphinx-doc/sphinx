"""Module to test type alias cross-reference resolution."""

from __future__ import annotations

import pathlib
from typing import Union

#: A type alias for paths - documented as py:data
PathLike = Union[str, pathlib.Path]  # noqa: UP007


def process_path(path: PathLike) -> str:
    """Process a path and return its string representation.

    This function signature references PathLike which should be cross-referenceable
    even though PathLike is documented as py:data, not py:class.
    """
    return str(path)
