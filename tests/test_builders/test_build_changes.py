"""Test the ChangesBuilder class."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('changes', testroot='changes')
def test_build(app: SphinxTestApp) -> None:
    app.build()

    # TODO: Use better checking of html content
    htmltext = (app.outdir / 'changes.html').read_text(encoding='utf8')
    assert 'Added in version 0.6: Some funny stuff.' in htmltext
    assert 'Changed in version 0.6: Even more funny stuff.' in htmltext
    assert 'Deprecated since version 0.6: Boring stuff.' in htmltext

    path_html = (
        '<b>Path</b>: <i>deprecated:</i> Deprecated since version 0.6:'
        ' So, that was a bad idea it turns out.'
    )
    assert path_html in htmltext

    malloc_html = (
        '<b>void *Test_Malloc(size_t n)</b>: <i>changed:</i> Changed in version 0.6:'
        ' Can now be replaced with a different allocator.</a>'
    )
    assert malloc_html in htmltext


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
