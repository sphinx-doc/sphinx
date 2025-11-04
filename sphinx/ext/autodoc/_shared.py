"""Importer utilities for autodoc"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util.inspect import safe_getattr

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Literal, NoReturn, Protocol

    from sphinx.util.typing import _RestifyMode

    class _AttrGetter(Protocol):  # NoQA: PYI046
        def __call__(self, obj: Any, name: str, default: Any = ..., /) -> Any: ...


class _AutodocAttrGetter:
    """getattr() override for types such as Zope interfaces."""

    _attr_getters: Sequence[tuple[type, Callable[[Any, str, Any], Any]]]

    __slots__ = ('_attr_getters',)

    def __init__(
        self, attr_getters: dict[type, Callable[[Any, str, Any], Any]], /
    ) -> None:
        super().__setattr__('_attr_getters', tuple(attr_getters.items()))

    def __call__(self, obj: Any, name: str, *defargs: Any) -> Any:
        for typ, func in self._attr_getters:
            if isinstance(obj, typ):
                return func(obj, name, *defargs)

        return safe_getattr(obj, name, *defargs)

    def __repr__(self) -> str:
        return f'_AutodocAttrGetter({dict(self._attr_getters)!r})'

    def __setattr__(self, key: str, value: Any) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __delattr__(self, key: str) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)


def _get_render_mode(
    typehints_format: Literal['fully-qualified', 'short'],
    /,
) -> _RestifyMode:
    if typehints_format == 'short':
        return 'smart'
    return 'fully-qualified-except-typing'
