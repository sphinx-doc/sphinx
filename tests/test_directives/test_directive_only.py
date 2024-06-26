"""Test the only directive with the test root."""

import re

import pytest
from docutils import nodes


@pytest.mark.sphinx('text', testroot='directive-only')
def test_sectioning(app, status, warning):
    app.build(filenames=[app.srcdir / 'only.rst'])
    doctree = app.env.get_doctree('only')
    app.env.apply_post_transforms(doctree, 'only')

    parts = _get_sections(doctree)
    for i, section in enumerate(parts):
        _test_sections(f'{i + 1}.', section, 4)
    assert len(parts) == 4, 'Expected 4 document level headings, got:\n%s' % \
        '\n'.join(p[0] for p in parts)


def _get_sections(section: nodes.Node):
    if not isinstance(section, nodes.section):
        return list(map(_get_sections, section.children))
    title = section.next_node(nodes.title).astext().strip()
    subsections = []
    children = section.children.copy()
    while children:
        node = children.pop(0)
        if isinstance(node, nodes.section):
            subsections.append(node)
            continue
        children = list(node.children) + children
    return [title, list(map(_get_sections, subsections))]


def _test_sections(prefix: str, sections, indent=0):
    title = sections[0]
    parent_num = title.split()[0]
    assert prefix == parent_num, f'Section out of place: {title!r}'
    for i, subsection in enumerate(sections[1]):
        num = subsection[0].split()[0]
        assert re.match('[0-9]+[.0-9]*[.]', num), f'Unnumbered section: {subsection[0]!r}'
        _test_sections(f'{prefix}{i + 1}.', subsection, indent + 4)
