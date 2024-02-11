from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from html5lib import HTMLParser

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from _pytest.config import Config
    from _pytest.main import Session
    from _pytest.nodes import Item


def pytest_collection_modifyitems(
    session: Session, config: Config, items: Sequence[Item]
) -> None:
    for item in items:
        if (
            'tests/test_builders/test_build_linkcheck.py' in str(item.path)
            and not item.get_closest_marker('parallel')
        ):
            # force serial execution of items in 'test_build_linkcheck.py'
            item.add_marker('serial')


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
