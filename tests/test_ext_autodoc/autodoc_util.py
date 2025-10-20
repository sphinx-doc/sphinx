from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

from sphinx.ext.autodoc._directive_options import (
    _AutoDocumenterOptions,
    _process_documenter_options,
)

# NEVER import those objects from sphinx.ext.autodoc directly
from sphinx.ext.autodoc.directive import DocumenterBridge
from sphinx.ext.autodoc.importer import _load_object_by_name
from sphinx.util.docutils import LoggingReporter
from sphinx.util.inspect import safe_getattr

if TYPE_CHECKING:
    from typing import Any

    from docutils.statemachine import StringList

    from sphinx.application import Sphinx
    from sphinx.ext.autodoc._property_types import _AutodocObjType


def do_autodoc(
    app: Sphinx,
    obj_type: _AutodocObjType,
    name: str,
    options: dict[str, Any] | None = None,
) -> StringList:
    options = {} if options is None else options.copy()
    if not app.env.current_document.docname:
        app.env.current_document.docname = 'index'  # set dummy docname
    doccls = app.registry.documenters[obj_type]
    opts = _process_documenter_options(
        option_spec=doccls.option_spec,
        default_options=app.config.autodoc_default_options,
        options=options,
    )
    docoptions = _AutoDocumenterOptions.from_directive_options(opts)
    state = Mock()
    bridge = DocumenterBridge(
        app.env, LoggingReporter(''), docoptions, 1, state, safe_getattr
    )
    documenter = doccls(bridge, name)
    props = _load_object_by_name(
        name=name,
        objtype=obj_type,
        mock_imports=app.config.autodoc_mock_imports,
        type_aliases=app.config.autodoc_type_aliases,
        current_document=app.env.current_document,
        config=app.config,
        env=app.env,
        events=app.events,
        get_attr=safe_getattr,
        options=documenter.options,
    )
    if props is not None:
        documenter.props = props
        documenter._generate()
    return bridge.result
