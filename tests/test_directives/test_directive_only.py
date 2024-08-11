"""Test the only directive with the test root."""

import re

import pytest
from docutils import nodes


@pytest.mark.sphinx('text', testroot='directive-only')
def test_sectioning(app):
    def getsects(section):
        if not isinstance(section, nodes.section):
            return [getsects(n) for n in section.children]
        title = section.next_node(nodes.title).astext().strip()
        subsects = []
        children = section.children[:]
        while children:
            node = children.pop(0)
            if isinstance(node, nodes.section):
                subsects.append(node)
                continue
            children = list(node.children) + children
        return [title, [getsects(subsect) for subsect in subsects]]

    def testsects(prefix, sects, indent=0):
        title = sects[0]
        parent_num = title.split()[0]
        assert prefix == parent_num, f'Section out of place: {title!r}'
        for i, subsect in enumerate(sects[1]):
            num = subsect[0].split()[0]
            assert re.match(
                '[0-9]+[.0-9]*[.]', num
            ), f'Unnumbered section: {subsect[0]!r}'
            testsects(prefix + str(i + 1) + '.', subsect, indent + 4)

    app.build(filenames=[app.srcdir / 'only.rst'])
    doctree = app.env.get_doctree('only')
    app.env.apply_post_transforms(doctree, 'only')

    parts = [
        getsects(n)
        for n in [_n for _n in doctree.children if isinstance(_n, nodes.section)]
    ]
    for i, s in enumerate(parts):
        testsects(str(i + 1) + '.', s, 4)
    actual_headings = '\n'.join(p[0] for p in parts)
    assert (
        len(parts) == 4
    ), f'Expected 4 document level headings, got:\n{actual_headings}'
