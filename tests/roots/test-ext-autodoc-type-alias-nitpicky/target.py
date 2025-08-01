"""Module to test type alias cross-reference resolution."""
from __future__ import annotations
import pathlib

#: Any type of path
pathlike = str | pathlib.Path


def read_file(path: pathlike) -> bytes:
    """Read a file and return its contents."""
    with open(path, "rb") as f:
        return f.read()