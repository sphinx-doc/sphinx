from __future__ import annotations

from datetime import datetime
from typing import Any  # NoQA: TC003

CONSTANT = 'foo'
SENTINEL = object()


def foo(
    name: str = CONSTANT,
    sentinel: Any = SENTINEL,
    now: datetime = datetime.now(),  # NoQA: B008,DTZ005
    color: int = 0xFFFFFF,
    *,
    kwarg1,
    kwarg2=0xFFFFFF,
) -> None:
    """docstring"""


class Class:
    """docstring"""

    def meth(
        self,
        name: str = CONSTANT,
        sentinel: Any = SENTINEL,
        now: datetime = datetime.now(),  # NoQA: B008,DTZ005
        color: int = 0xFFFFFF,
        *,
        kwarg1,
        kwarg2=0xFFFFFF,
    ) -> None:
        """docstring"""

    @classmethod
    def clsmeth(
        cls,
        name: str = CONSTANT,
        sentinel: Any = SENTINEL,
        now: datetime = datetime.now(),  # NoQA: B008,DTZ005
        color: int = 0xFFFFFF,
        *,
        kwarg1,
        kwarg2=0xFFFFFF,
    ) -> None:
        """docstring"""


get_sentinel = lambda custom=SENTINEL: custom  # NoQA: E731
"""docstring"""


class MultiLine:
    """docstring"""

    # The properties will raise a silent SyntaxError because "lambda self: 1"
    # will be detected as a function to update the default values of. However,
    # only prop3 will not fail because it's on a single line whereas the others
    # will fail to parse.

    # fmt: off
    prop1 = property(
      lambda self: 1, doc='docstring')

    prop2 = property(
      lambda self: 2, doc='docstring'
    )

    prop3 = property(lambda self: 3, doc='docstring')

    prop4 = (property
    (lambda self: 4, doc='docstring'))

    prop5 = property\
    (lambda self: 5, doc='docstring')  # NoQA: E211
    # fmt: on
