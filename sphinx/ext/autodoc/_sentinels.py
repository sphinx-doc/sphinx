from __future__ import annotations

TYPE_CHECKING = False
if TYPE_CHECKING:
    from typing import NoReturn


class _Sentinel:
    """Create a unique sentinel object."""

    def __init__(self, name: str, /) -> None:
        self._name = name

    def __repr__(self) -> str:
        return f'<{self._name}>'

    def __or__(self, other: object) -> type[_Sentinel | object]:
        return self | other

    def __ror__(self, other: object) -> type[object | _Sentinel]:
        return other | self

    def __getstate__(self) -> NoReturn:
        msg = f'Cannot pickle {type(self).__name__!r} object'
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


ALL = _All('ALL')
EMPTY = _Empty('EMPTY')
UNINITIALIZED_ATTR = _Sentinel('UNINITIALIZED_ATTR')
INSTANCE_ATTR = _Sentinel('INSTANCE_ATTR')
SLOTS_ATTR = _Sentinel('SLOTS_ATTR')
SUPPRESS = _Sentinel('SUPPRESS')
