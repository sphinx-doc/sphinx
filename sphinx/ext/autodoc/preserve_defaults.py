"""Preserve function defaults.

Preserve the default argument values of function signatures in source code
and keep them not evaluated for readability.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.ext.autodoc._dynamic._preserve_defaults import (
    DefaultValue as DefaultValue,  # NoQA: PLC0414
)
from sphinx.ext.autodoc._dynamic._preserve_defaults import (
    _get_arguments as _get_arguments,  # NoQA: PLC0414
)
from sphinx.ext.autodoc._dynamic._preserve_defaults import (
    _get_arguments_inner as _get_arguments_inner,  # NoQA: PLC0414
)
from sphinx.ext.autodoc._dynamic._preserve_defaults import (
    _is_lambda as _is_lambda,  # NoQA: PLC0414
)
from sphinx.ext.autodoc._dynamic._preserve_defaults import (
    get_default_value as get_default_value,  # NoQA: PLC0414
)
from sphinx.ext.autodoc._dynamic._preserve_defaults import update_default_value
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any

    from sphinx.application import Sphinx

logger = logging.getLogger(__name__)


# Retained: legacy class-based
def update_defvalue(app: Sphinx, obj: Any, bound_method: bool) -> None:
    """Update defvalue info of *obj* using type_comments."""
    if not app.config.autodoc_preserve_defaults:
        return

    update_default_value(obj, bound_method)
