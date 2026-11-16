from typing import Union

__all__ = ['V1', 'V2']

#: v1
V1 = str | int

#: v2
V2 = Union[str, int]  # ruff: ignore[non-pep604-annotation-union]


class Container:
    #: class-level pep 604
    V1 = str | int

    #: class-level typing.Union
    V2 = Union[str, int]  # ruff: ignore[non-pep604-annotation-union]
