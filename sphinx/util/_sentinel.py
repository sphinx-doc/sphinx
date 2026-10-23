from __future__ import annotations

import sys

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import Self, _SpecialForm

if sys.version_info[:2] >= (3, 15):
    from builtins import sentinel as sentinel  # ruff: ignore[useless-import-alias]
elif TYPE_CHECKING:
    from typing_extensions import sentinel as sentinel  # ruff: ignore[useless-import-alias]
else:

    class sentinel:
        """Create a unique sentinel object."""

        _name: str

        def __init__(self, name: str, /) -> Self:
            self._name = name
            self.__module__ = sys._getframemodulename(1) or '__main__'

        def __setattr__(self, attr: str, value: object) -> None:
            if attr not in {'_name', '__module__'}:
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

        def __reduce__(self) -> str:
            return self._name
