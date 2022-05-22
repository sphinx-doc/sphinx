import pathlib
from typing import Any, Tuple, TypeVar, Union

CONST1: int
#: docstring
CONST2: int = 1
#: docstring
CONST3: pathlib.PurePosixPath = pathlib.PurePosixPath("/a/b/c")
#: docstring
T = TypeVar("T", bound=pathlib.PurePosixPath)


def incr(a: int, b: int = 1) -> int:
    return a + b


def decr(a, b = 1):
    # type: (int, int) -> int
    return a - b


class Math:
    CONST1: int
    CONST2: int = 1
    CONST3: pathlib.PurePosixPath = pathlib.PurePosixPath("/a/b/c")

    def __init__(self, s: str, o: Any = None) -> None:
        pass

    def incr(self, a: int, b: int = 1) -> int:
        return a + b

    def decr(self, a, b = 1):
        # type: (int, int) -> int
        return a - b

    def nothing(self):
        # type: () -> None
        pass

    def horse(self,
              a,  # type: str
              b,  # type: int
              ):
        # type: (...) -> None
        return

    @property
    def prop(self) -> int:
        return 0

    @property
    def path(self) -> pathlib.PurePosixPath:
        return pathlib.PurePosixPath("/a/b/c")


def tuple_args(x: Tuple[int, Union[int, str]]) -> Tuple[int, int]:
    pass


class NewAnnotation:
    def __new__(cls, i: int) -> 'NewAnnotation':
        pass


class NewComment:
    def __new__(cls, i):
        # type: (int) -> NewComment
        pass


class _MetaclassWithCall(type):
    def __call__(cls, a: int):
        pass


class SignatureFromMetaclass(metaclass=_MetaclassWithCall):
    pass


def complex_func(arg1, arg2, arg3=None, *args, **kwargs):
    # type: (str, List[int], Tuple[int, Union[str, Unknown]], *str, **str) -> None
    pass


def missing_attr(c,
                 a,  # type: str
                 b=None  # type: Optional[str]
                 ):
    # type: (...) -> str
    return a + (b or "")


class _ClassWithDocumentedInit:
    """Class docstring."""

    def __init__(self, x: int, *args: int, **kwargs: int) -> None:
        """Init docstring.

        :param x: Some integer
        :param args: Some integer
        :param kwargs: Some integer
        """
