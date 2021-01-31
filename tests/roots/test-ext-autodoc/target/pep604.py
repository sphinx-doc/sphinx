from __future__ import annotations

attr: int | str  #: docstring


def sum(x: int | str, y: int | str) -> int | str:
    """docstring"""


class Foo:
    """docstring"""

    attr: int | str  #: docstring

    def meth(self, x: int | str, y: int | str) -> int | str:
        """docstring"""
