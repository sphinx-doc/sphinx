from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from html5lib import HTMLParser

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from pathlib import Path
    from xml.etree.ElementTree import Element

etree_cache: dict[Path, Element] = {}


def _parse(fname: Path) -> Element:
    if fname in etree_cache:
        return etree_cache[fname]
    with fname.open('rb') as fp:
        etree = HTMLParser(namespaceHTMLElements=False).parse(fp)
        etree_cache[fname] = etree
        return etree


@pytest.fixture(scope='package')
def cached_etree_parse() -> Generator[Callable[[Path], Element], None, None]:
    yield _parse
    etree_cache.clear()
