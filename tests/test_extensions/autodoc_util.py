from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

# NEVER import those objects from sphinx.ext.autodoc directly
from sphinx.ext.autodoc.directive import DocumenterBridge, process_documenter_options
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
    app.env.temp_data.setdefault('docname', 'index')  # set dummy docname
    doccls = app.registry.documenters[objtype]
    docoptions = process_documenter_options(doccls, app.config, options)
    state = Mock()
    state.document.settings.tab_width = 8
    bridge = DocumenterBridge(app.env, LoggingReporter(''), docoptions, 1, state)
    documenter = doccls(bridge, name)
    documenter.generate()
    return bridge.result
