from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from xml.etree.ElementTree import Element


def _intradocument_hyperlink_check(nodes: Sequence[Element]) -> None:
    """Confirm that a series of nodes are all HTML hyperlinks to the current page"""
    assert nodes, 'Expected at least one node to check'
    for node in nodes:
        assert node.tag == 'a', 'Attempted to check hyperlink on a non-anchor element'
        href = node.attrib.get('href')
        # Allow Sphinx index and table hyperlinks to be non-same-document, as exceptions.
        if href in {'genindex.html', 'py-modindex.html', 'search.html'}:
            continue
        assert not href or href.startswith('#'), 'Hyperlink failed same-document check'
