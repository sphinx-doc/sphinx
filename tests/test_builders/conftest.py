from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.testing.util import etree_parse

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path
    from xml.etree.ElementTree import ElementTree

_etree_cache: dict[Path, ElementTree] = {}


def _parse(path: Path) -> ElementTree:
    if path in _etree_cache:
        return _etree_cache[path]

    _etree_cache[path] = tree = etree_parse(path)
    return tree


@pytest.fixture(scope='package')
def cached_etree_parse() -> Iterator[Callable[[Path], ElementTree]]:
    yield _parse
    _etree_cache.clear()
