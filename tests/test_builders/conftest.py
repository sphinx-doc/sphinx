from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import etree_html_parse

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path

    from lxml.etree import _ElementTree

etree_cache: dict[Path, _ElementTree] = {}


def _etree_parse(source: Path) -> _ElementTree:
    if source in etree_cache:
        return etree_cache[source]

    # do not use etree_cache.setdefault() to avoid calling lxml.html.parse()
    etree_cache[source] = tree = etree_html_parse(source)
    return tree


@pytest.fixture(scope='package')
def cached_etree_parse() -> Generator[Callable[[Path], _ElementTree], None, None]:
    """Provide caching for :func:`sphinx.testing.util.etree_html_parse`."""
    yield _etree_parse
    etree_cache.clear()
