from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from sphinx.environment import _CurrentDocument
from sphinx.events import EventManager
from sphinx.ext.autodoc._directive_options import _process_documenter_options
from sphinx.ext.autodoc._generate import _auto_document_object
from sphinx.ext.autodoc._shared import _AutodocConfig
from sphinx.util.inspect import safe_getattr

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from typing import Any

    from sphinx.ext.autodoc._property_types import _AutodocObjType

_DEFAULT_CONFIG = _AutodocConfig()


class FakeEvents(EventManager):
    def __init__(self) -> None:
        super().__init__(SimpleNamespace(pdb=False))  # type: ignore[arg-type]

        self.add('autodoc-before-process-signature')
        self.add('autodoc-process-docstring')
        self.add('autodoc-process-signature')
        self.add('autodoc-skip-member')
        self.add('autodoc-process-bases')
        self.add('object-description-transform')

    def connect(
        self, name: str, callback: Callable[..., Any], priority: int = 500
    ) -> int:
        return super().connect(name, callback, priority)


def do_autodoc(
    obj_type: _AutodocObjType,
    name: str,
    *,
    config: _AutodocConfig = _DEFAULT_CONFIG,
    current_document: _CurrentDocument | None = None,
    events: FakeEvents | None = None,
    expect_import_error: bool = False,
    options: dict[str, Any] | None = None,
    ref_context: Mapping[str, str | None] | None = None,
) -> list[str]:
    if current_document is None:
        current_document = _CurrentDocument(docname='index')
    if events is None:
        events = FakeEvents()
    if ref_context is None:
        ref_context = {}
    reread_always: set[str] = set()

    options = {} if options is None else options.copy()
    doc_options = _process_documenter_options(
        obj_type=obj_type,
        default_options=config.autodoc_default_options,
        options=options,
    )

    content = _auto_document_object(
        name=name,
        obj_type=obj_type,
        config=config,
        current_document=current_document,
        events=events,
        get_attr=safe_getattr,
        more_content=None,
        options=doc_options,
        record_dependencies=set(),
        ref_context=ref_context,
        reread_always=reread_always,
    )
    if expect_import_error:
        assert content is None
        return []

    assert content is not None
    return content.data
