from __future__ import annotations

import pytest
from html5lib import HTMLParser
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

etree_cache = {}


def _parse(fname: Path) -> HTMLParser:
    if fname in etree_cache:
        return etree_cache[fname]
    with fname.open('rb') as fp:
        etree = HTMLParser(namespaceHTMLElements=False).parse(fp)
        etree_cache[fname] = etree
        return etree


@pytest.fixture(scope='package')
def cached_etree_parse():
    yield _parse
    etree_cache.clear()
