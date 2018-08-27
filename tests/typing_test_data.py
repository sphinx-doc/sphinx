from numbers import Integral
from typing import Any, List, TypeVar, Union, Callable, Tuple, Optional


def f0(x: int, y: Integral) -> None:
    pass


def f1(x: List[int]) -> List[int]:
    pass


T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)


def f2(x: List[T], y: List[T_co], z: T) -> List[T_contra]:
    pass


def f3(x: Union[str, Integral]) -> None:
    pass


MyStr = str


def f4(x: 'MyStr', y: MyStr) -> None:
    pass


def f5(x: int, *, y: str, z: str) -> None:
    pass


def f6(x: int, *args, y: str, z: str) -> None:
    pass


def f7(x: int = None, y: dict = {}) -> None:
    pass


def f8(x: Callable[[int, str], int]) -> None:
    # See https://github.com/ambv/typehinting/issues/149 for Callable[..., int]
    pass


def f9(x: Callable) -> None:
    pass


def f10(x: Tuple[int, str], y: Tuple[int, ...]) -> None:
    pass


class CustomAnnotation:
    def __repr__(self):
        return 'CustomAnnotation'


def f11(x: CustomAnnotation(), y: 123) -> None:
    pass


def f12() -> Tuple[int, str, int]:
    pass


def f13() -> Optional[str]:
    pass


def f14() -> Any:
    pass


class Node:
    def __init__(self, parent: Optional['Node']) -> None:
        pass

    def children(self) -> List['Node']:
        pass
