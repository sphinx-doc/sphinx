from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, Literal, Protocol, TypedDict

    from sphinx.builders.html._assets import _CascadingStyleSheet, _JavaScript

    class _NavigationRelation(TypedDict):
        link: str
        title: str

    class _GlobalContextHTML(TypedDict):
        embedded: bool
        project: str
        release: str
        version: str
        last_updated: str | None
        copyright: str
        master_doc: str
        root_doc: str
        use_opensearch: bool
        docstitle: str | None
        shorttitle: str
        show_copyright: bool
        show_search_summary: bool
        show_sphinx: bool
        has_source: bool
        show_source: bool
        sourcelink_suffix: str
        file_suffix: str
        link_suffix: str
        script_files: Sequence[_JavaScript]
        language: str | None
        css_files: Sequence[_CascadingStyleSheet]
        sphinx_version: str
        sphinx_version_tuple: tuple[int, int, int, str, int]
        docutils_version_info: tuple[int, int, int, str, int]
        styles: Sequence[str]
        rellinks: Sequence[tuple[str, str, str, str]]
        builder: str
        parents: Sequence[_NavigationRelation]
        logo_url: str
        logo_alt: str
        favicon_url: str
        html5_doctype: Literal[True]

    class _PathtoCallable(Protocol):
        def __call__(
            self, otheruri: str, resource: bool = False, baseuri: str = ...
        ) -> str: ...

    class _ToctreeCallable(Protocol):
        def __call__(self, **kwargs: Any) -> str: ...

    class _PageContextHTML(_GlobalContextHTML):
        # get_doc_context()
        prev: Sequence[_NavigationRelation]
        next: Sequence[_NavigationRelation]
        title: str
        meta: dict[str, Any] | None
        body: str
        metatags: str
        sourcename: str
        toc: str
        display_toc: bool
        page_source_suffix: str

        # handle_page()
        pagename: str
        current_page_name: str
        encoding: str
        pageurl: str | None
        pathto: _PathtoCallable
        hasdoc: Callable[[str], bool]
        toctree: _ToctreeCallable
        content_root: str
        css_tag: Callable[[_CascadingStyleSheet], str]
        js_tag: Callable[[_JavaScript], str]

        # add_sidebars()
        sidebars: Sequence[str] | None

else:
    _NavigationRelation = dict
    _GlobalContextHTML = dict
    _PageContextHTML = dict
