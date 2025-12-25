"""Test the only directive with the test root."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest
from docutils import nodes

if TYPE_CHECKING:
    from typing import Any

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('text', testroot='directive-only')
def test_sectioning(app: SphinxTestApp) -> None:
    app.build(filenames=[app.srcdir / 'only.rst'])
    doctree = app.env.get_doctree('only')
    app.env.apply_post_transforms(doctree, 'only')

    parts = [_get_sections(n) for n in doctree.children if isinstance(n, nodes.section)]
    for i, section in enumerate(parts):
        _test_sections(f'{i + 1}.', section, 4)
    actual_headings = '\n'.join(p[0] for p in parts)  # type: ignore[misc]
    assert len(parts) == 4, (
        f'Expected 4 document level headings, got:\n{actual_headings}'
    )


def _get_sections(section: nodes.Node) -> list[str | list[Any]]:
    if not isinstance(section, nodes.section):
        return list(map(_get_sections, section.children))
    next_title_node = section.next_node(nodes.title)
    assert next_title_node is not None
    title = next_title_node.astext().strip()
    subsections = []
    children = section.children.copy()
    while children:
        node = children.pop(0)
        if isinstance(node, nodes.section):
            subsections.append(node)
            continue
        children = list(node.children) + children
    return [title, list(map(_get_sections, subsections))]


def _test_sections(
    prefix: str, sections: list[str | list[Any]], indent: int = 0
) -> None:
    title = sections[0]
    assert isinstance(title, str)
    parent_num = title.partition(' ')[0]
    assert prefix == parent_num, f'Section out of place: {title!r}'
    for i, subsection in enumerate(sections[1]):
        subsection_title = subsection[0]
        assert isinstance(subsection_title, str)
        num = subsection_title.partition(' ')[0]
        assert re.match('[0-9]+[.0-9]*[.]', num), (
            f'Unnumbered section: {subsection[0]!r}'
        )
        _test_sections(f'{prefix}{i + 1}.', subsection, indent + 4)
