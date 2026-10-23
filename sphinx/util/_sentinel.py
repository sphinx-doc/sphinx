from __future__ import annotations

import sys

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import NoReturn, Self, _SpecialForm

if sys.version_info[:2] >= (3, 15):
    from builtins import sentinel as sentinel
elif TYPE_CHECKING:
    from typing_extensions import sentinel as sentinel
else:

    class sentinel:
        """Create a unique sentinel object."""

        __slots__ = ('_name',)

        _name: str

        def __new__(cls, name: str, /) -> Self:
            sentinel = super().__new__(cls)
            object.__setattr__(sentinel, '_name', name)
            return sentinel

        def __setattr__(self, attr: str, value: object) -> None:
            msg = f'{self._name} is immutable'
            raise AttributeError(msg)

        def __repr__(self) -> str:
            return self._name

        def __or__(self, other: object) -> _SpecialForm:
            from typing import Union

            return Union[self, other]  # ruff: ignore[non-pep604-annotation-union]  # ty: ignore[invalid-type-form, invalid-return-type]

        def __ror__(self, other: object) -> _SpecialForm:
            from typing import Union

            return Union[other, self]  # ruff: ignore[non-pep604-annotation-union]  # ty: ignore[invalid-type-form, invalid-return-type]

        def __getstate__(self) -> NoReturn:
            msg = f'Cannot pickle {self._name}'
            raise TypeError(msg)
