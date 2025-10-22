from __future__ import annotations

from typing import TYPE_CHECKING

from docutils.statemachine import StringList

from sphinx.ext.autodoc._directive_options import (
    _AutoDocumenterOptions,
    _process_documenter_options,
)
from sphinx.ext.autodoc._generate import _generate_directives
from sphinx.ext.autodoc.importer import _load_object_by_name
from sphinx.util.inspect import safe_getattr

if TYPE_CHECKING:
    from typing import Any

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
    option_spec = app.registry.documenters[obj_type].option_spec
    opts = _process_documenter_options(
        option_spec=option_spec,
        default_options=app.config.autodoc_default_options,
        options=options,
    )
    doc_options = _AutoDocumenterOptions.from_directive_options(opts)

    config = app.config
    current_document = app.env.current_document
    env = app.env
    events = app.events
    props = _load_object_by_name(
        name=name,
        objtype=obj_type,
        mock_imports=config.autodoc_mock_imports,
        type_aliases=config.autodoc_type_aliases,
        current_document=current_document,
        config=config,
        env=env,
        events=events,
        get_attr=safe_getattr,
        options=doc_options,
    )
    result = StringList()
    if props is not None:
        _generate_directives(
            config=config,
            current_document=current_document,
            env=env,
            events=events,
            get_attr=safe_getattr,
            indent='',
            options=doc_options,
            props=props,
            record_dependencies=set(),
            result=result,
        )
    return result
