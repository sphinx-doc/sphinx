"""Test output of reference URIs when building single-page HTML output."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.test_builders.xpath_util import check_xpath

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path
    from xml.etree.ElementTree import Element, ElementTree

    from sphinx.testing.util import SphinxTestApp


def _internal_reference_fragment_check(nodes: Sequence[Element]) -> None:
    """Confirm that internal references do not contain duplicate fragment symbols"""
    assert nodes, 'Expected at least one node to check'
    for node in nodes:
        assert node.tag == 'a', 'Attempted to check hyperlink on a non-anchor element'
        href = node.attrib.get('href')
        # Allow Sphinx index and table hyperlinks to be non-same-document, as exceptions.
        if href in {'genindex.html', 'py-modindex.html', 'search.html'}:
            continue
        assert not href or href.count('#') < 2, 'Hyperlink contains duplicate fragments'


@pytest.mark.sphinx('singlehtml', testroot='refuris')
def test_singlehtml_refuris(
    app: SphinxTestApp,
    cached_etree_parse: Callable[[Path], ElementTree],
) -> None:
    app.build()
    check_xpath(
        cached_etree_parse(app.outdir / 'index.html'),
        'index.html',
        ".//a[@class='reference internal']",
        _internal_reference_fragment_check,
    )
