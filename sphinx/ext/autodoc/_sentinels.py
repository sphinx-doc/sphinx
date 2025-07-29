from __future__ import annotations

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import NoReturn, Self, _SpecialForm


class _Sentinel:
    """Create a unique sentinel object."""

    __slots__ = ('_name',)

    _name: str

    def __new__(cls, name: str, /) -> Self:
        sentinel = super().__new__(cls)
        object.__setattr__(sentinel, '_name', str(name))
        return sentinel

    def __repr__(self) -> str:
        return self._name

    def __setattr__(self, key: str, value: object) -> NoReturn:
        msg = f'{self._name} is immutable'
        raise AttributeError(msg)

    def __or__(self, other: object) -> _SpecialForm:
        from typing import Union

        return Union[self, other]  # NoQA: UP007

    def __ror__(self, other: object) -> _SpecialForm:
        from typing import Union

        return Union[other, self]  # NoQA: UP007

    def __getstate__(self) -> NoReturn:
        msg = f'Cannot pickle {self._name}'
        raise TypeError(msg)


class _All(_Sentinel):
    """A special value for :*-members: that matches to any member."""

    def __contains__(self, item: object) -> bool:
        return True

    def append(self, item: object) -> None:
        pass  # nothing


class _Empty(_Sentinel):
    """A special value for :exclude-members: that never matches to any member."""

    def __contains__(self, item: object) -> bool:
        return False


if TYPE_CHECKING:
    # For the sole purpose of satisfying the type checker.
    # fmt: off
    class ALL: ...
    class EMPTY: ...
    class INSTANCE_ATTR: ...
    class RUNTIME_INSTANCE_ATTRIBUTE: ...
    class SLOTS_ATTR: ...
    class SUPPRESS: ...
    class UNINITIALIZED_ATTR: ...
    # fmt: on
else:
    ALL = _All('ALL')
    EMPTY = _Empty('EMPTY')
    INSTANCE_ATTR = _Sentinel('INSTANCE_ATTR')
    RUNTIME_INSTANCE_ATTRIBUTE = _Sentinel('RUNTIME_INSTANCE_ATTRIBUTE')
    SLOTS_ATTR = _Sentinel('SLOTS_ATTR')
    SUPPRESS = _Sentinel('SUPPRESS')
    UNINITIALIZED_ATTR = _Sentinel('UNINITIALIZED_ATTR')
