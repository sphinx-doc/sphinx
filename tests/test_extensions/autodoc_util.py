from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from sphinx.ext.autodoc._directive_options import (
    _AutoDocumenterOptions,
    _process_documenter_options,
)

# NEVER import those objects from sphinx.ext.autodoc directly
from sphinx.ext.autodoc.directive import DocumenterBridge
from sphinx.util.docutils import LoggingReporter

if TYPE_CHECKING:
    from typing import Any

    from docutils.statemachine import StringList

    from sphinx.application import Sphinx


def do_autodoc(
    app: Sphinx,
    objtype: str,
    name: str,
    options: dict[str, Any] | None = None,
) -> StringList:
    options = {} if options is None else options.copy()
    if not app.env.current_document.docname:
        app.env.current_document.docname = 'index'  # set dummy docname
    doccls = app.registry.documenters[objtype]
    opts = _process_documenter_options(
        option_spec=doccls.option_spec,
        default_options=app.config.autodoc_default_options,
        options=options,
    )
    docoptions = _AutoDocumenterOptions.from_directive_options(opts)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return bridge.result
