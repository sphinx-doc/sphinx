"""Evaluate annotations with contexts supplied by autodoc extensions."""

from __future__ import annotations

from contextlib import ExitStack
from typing import TYPE_CHECKING

from sphinx.util.typing import get_type_hints

if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import Any

    from sphinx.events import EventManager


def _get_type_hints(
    events: EventManager,
    obj: Any,
    globalns: dict[str, Any] | None = None,
    localns: Mapping[str, Any] | None = None,
    *,
    include_extras: bool = False,
) -> dict[str, Any]:
    with ExitStack() as stack:
        for context in events.emit('autodoc-type-hints-context', obj):
            if context is not None:
                stack.enter_context(context)
        return get_type_hints(obj, globalns, localns, include_extras=include_extras)
