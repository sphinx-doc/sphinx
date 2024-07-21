from __future__ import annotations

from typing import Callable, List

#: A list of int
T1 = List[int]

T2 = List[int]
"""Another list of int."""

T3 = List[int]  # a generic alias not having a doccomment

C = Callable[[int], None]  # a generic alias not having a doccomment


class Class:
    #: A list of int
    T1 = List[int]

    T2 = List[int]
    """Another list of int."""

    T3 = List[int]


#: A list of Class
L1 = List[Class]

L2 = List[Class]  # a generic alias not having a doccomment
