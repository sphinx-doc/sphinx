from datetime import datetime
from typing import Any

CONSTANT = 'foo'
SENTINEL = object()


def foo(name: str = CONSTANT,
        sentinel: Any = SENTINEL,
        now: datetime = datetime.now(),
        color: int = 0xFFFFFF,
        *,
        kwarg1,
        kwarg2 = 0xFFFFFF) -> None:
    """docstring"""


class Class:
    """docstring"""

    def meth(self, name: str = CONSTANT, sentinel: Any = SENTINEL,
             now: datetime = datetime.now(), color: int = 0xFFFFFF,
             *, kwarg1, kwarg2 = 0xFFFFFF) -> None:
        """docstring"""

    @classmethod
    def clsmeth(cls, name: str = CONSTANT, sentinel: Any = SENTINEL,
                now: datetime = datetime.now(), color: int = 0xFFFFFF,
                *, kwarg1, kwarg2 = 0xFFFFFF) -> None:
        """docstring"""
