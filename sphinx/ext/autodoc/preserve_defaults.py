"""Preserve function defaults.

Preserve the default argument values of function signatures in source code
and keep them not evaluated for readability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.ext.autodoc._dynamic._preserve_defaults import (
    DefaultValue,  # ruff: ignore[unused-import]
    _get_arguments,  # ruff: ignore[unused-import]
    _get_arguments_inner,  # ruff: ignore[unused-import]
    _is_lambda,  # ruff: ignore[unused-import]
    get_default_value,  # ruff: ignore[unused-import]
    update_default_value,
)

if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx


# Retained: legacy class-based
def update_defvalue(app: Sphinx, obj: Any, bound_method: bool) -> None:
    """Update defvalue info of *obj* using type_comments."""
    if not app.config.autodoc_preserve_defaults:
        return

    update_default_value(obj, bound_method)
