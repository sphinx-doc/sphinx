"""Sphinx test comparer for pytest"""
from __future__ import annotations

import difflib
import pathlib
from typing import Any


class PathComparer:
    """
    OS-independent path comparison.

    Windows path sep and posix path sep:

    >>> '\\to\\index' == PathComparer('/to/index')
    True
    >>> '\\to\\index' == PathComparer('/to/index2')
    False

    Windows path with drive letters

    >>> 'C:\\to\\index' == PathComparer('/to/index')
    True
    >>> 'C:\\to\\index' == PathComparer('C:/to/index')
    True
    >>> 'C:\\to\\index' == PathComparer('D:/to/index')
    False
    """
    def __init__(self, path: str | pathlib.Path):
        """
        :param str path: path string, it will be cast as pathlib.Path.
        """
        self.path = pathlib.Path(path)

    def __str__(self) -> str:
        return self.path.as_posix()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: '{self}'>"

    def __eq__(self, other: str | pathlib.Path) -> bool:  # type: ignore
        return not bool(self.ldiff(other))

    def diff(self, other: str | pathlib.Path) -> list[str]:
        """compare self and other.

        When different is not exist, return empty list.

        >>> PathComparer('/to/index').diff('C:\\to\\index')
        []

        When different is exist, return unified diff style list as:

        >>> PathComparer('/to/index').diff('C:\\to\\index2')
        [
           '- C:/to/index'
           '+ C:/to/index2'
           '?            +'
        ]
        """
        return self.ldiff(other)

    def ldiff(self, other: str | pathlib.Path) -> list[str]:
        return self._diff(
            self.path,
            pathlib.Path(other),
        )

    def rdiff(self, other: str | pathlib.Path) -> list[str]:
        return self._diff(
            pathlib.Path(other),
            self.path,
        )

    def _diff(self, lhs: pathlib.Path, rhs: pathlib.Path) -> list[str]:
        if lhs == rhs:
            return []

        if lhs.drive or rhs.drive:
            # If either has a drive letter compare by absolute path
            s_path, o_path = lhs.absolute().as_posix(), rhs.absolute().as_posix()
        else:
            s_path, o_path = lhs.as_posix(), rhs.as_posix()

        if s_path == o_path:
            return []

        return [line.strip() for line in difflib.Differ().compare([s_path], [o_path])]


def pytest_assertrepr_compare(op: str, left: Any, right: Any) -> list[str]:
    if isinstance(left, PathComparer) and op == "==":
        return ['Comparing path:'] + left.ldiff(right)
    elif isinstance(right, PathComparer) and op == "==":
        return ['Comparing path:'] + right.rdiff(left)
    else:
        return []
