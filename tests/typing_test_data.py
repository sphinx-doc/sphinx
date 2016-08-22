from typing import List, TypeVar, Union, Callable, Tuple

from numbers import Integral


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


def f6(x: int = None, y: dict = {}) -> None:
    pass


def f7(x: Callable[[int, str], int]) -> None:
    # See https://github.com/ambv/typehinting/issues/149 for Callable[..., int]
    pass


def f8(x: Tuple[int, str], y: Tuple[int, ...]) -> None:
    pass


class CustomAnnotation:
    def __repr__(self):
        return 'CustomAnnotation'

def f9(x: CustomAnnotation(), y: 123) -> None:
    pass
