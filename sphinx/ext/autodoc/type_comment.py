"""Update annotations info of living objects using type_comments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.ext.autodoc._dynamic._type_comments import (
    _update_annotations_using_type_comments,
    not_suppressed,  # ruff: ignore[unused-import]
    signature_from_ast,  # ruff: ignore[unused-import]
)

if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx


# Retained: legacy class-based
def update_annotations_using_type_comments(
    app: Sphinx, obj: Any, bound_method: bool
) -> None:
    if not app.config.autodoc_use_type_comments:
        return None

    return _update_annotations_using_type_comments(obj, bound_method)
