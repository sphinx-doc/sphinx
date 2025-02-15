from __future__ import annotations

from os import path
from typing import Union


class Foo:
    class Bar:  # NoQA: D106
        pass

    def __init__(self) -> None:
        pass

    def bar(self) -> None:
        pass

    @property
    def baz(self) -> None:
        pass


def bar(x: int | str, y: int = 1) -> None:
    pass
