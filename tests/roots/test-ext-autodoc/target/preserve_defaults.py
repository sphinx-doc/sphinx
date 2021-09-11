from datetime import datetime
from typing import Any

CONSTANT = 'foo'
SENTINEL = object()


def foo(name: str = CONSTANT,
        sentinel: Any = SENTINEL,
        now: datetime = datetime.now()) -> None:
    """docstring"""


class Class:
    """docstring"""

    def meth(self, name: str = CONSTANT, sentinel: Any = SENTINEL,
             now: datetime = datetime.now()) -> None:
        """docstring"""
