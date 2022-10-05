from datetime import date
from typing import NewType, TypeVar

#: T1
T1 = TypeVar("T1")

T2 = TypeVar("T2")  # A TypeVar not having doc comment

#: T3
T3 = TypeVar("T3", int, str)

#: T4
T4 = TypeVar("T4", covariant=True)

#: T5
T5 = TypeVar("T5", contravariant=True)

#: T6
T6 = NewType("T6", date)

#: T7
T7 = TypeVar("T7", bound=int)


class Class:
    #: T1
    T1 = TypeVar("T1")

    #: T6
    T6 = NewType("T6", date)
