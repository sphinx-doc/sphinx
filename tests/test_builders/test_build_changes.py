"""Test the ChangesBuilder class."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp

import re   # <--- IMPORT ADDED

from bs4 import BeautifulSoup   # <--- IMPORT ADDED


@pytest.mark.sphinx('changes', testroot='changes')
def test_build(app: SphinxTestApp) -> None:
    """Test the 'changes' builder and resolve TODO for better HTML checking."""
    app.build()

    htmltext = (app.outdir / 'changes.html').read_text(encoding='utf8')
    soup = BeautifulSoup(htmltext, 'html.parser')

    def find_change_item(type_text: str, version: str, content: str) -> dict:
        """Helper to find and validate change items."""
        # Use regex to find text content, ignoring surrounding whitespace/newlines
        item = soup.find('li', string=re.compile(r'\s*' + re.escape(content) + r'\s*'))
        assert item is not None, f"Could not find change item containing '{content}'"

        type_elem = item.find('i')
        assert type_elem is not None, f"Missing type indicator for '{content}'"
        assert type_text in type_elem.text, f"Expected type '{type_text}' for '{content}'"

        assert f"version {version}" in item.text, f"Version {version} not found in '{content}'"

        return {'item': item, 'type': type_elem}

    # Test simple changes
    changes = [
        ('added', '0.6', 'Some funny stuff.'),
        ('changed', '0.6', 'Even more funny stuff.'),
        ('deprecated', '0.6', 'Boring stuff.')
    ]

    for change_type, version, content in changes:
        find_change_item(change_type, version, content)

    # Test Path deprecation (Search by unique text)
    path_change = find_change_item('deprecated', '0.6', 'So, that was a bad idea it turns out.')
    assert path_change['item'].find('b').text == 'Path'

    # Test Malloc function change (Search by unique text)
    malloc_change = find_change_item('changed', '0.6', 'Can now be replaced with a different allocator.')
    assert malloc_change['item'].find('b').text == 'void *Test_Malloc(size_t n)'

    # Test the other test function still works
    assert len(soup.find_all('li')) >= 5  # Make sure we found all items


@pytest.mark.sphinx(
    'changes',
    testroot='changes',
    srcdir='changes-none',
    confoverrides={'version': '0.7', 'release': '0.7b1'},
)
def test_no_changes(app: SphinxTestApp) -> None:
    app.build()

    assert 'no changes in version 0.7.' in app.status.getvalue()
    assert not (app.outdir / 'changes.html').exists()
