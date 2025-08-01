"""Test type alias cross-reference resolution in nitpicky mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx import addnodes

if TYPE_CHECKING:
    from typing import Any

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-autodoc-type-alias-xref')
def test_type_alias_xref_resolution(app: SphinxTestApp, warning: Any) -> None:
    """Test that type aliases documented as py:data can be cross-referenced as py:class."""
    app.build()

    # In nitpicky mode, check that no warnings were generated for type alias cross-references
    warnings_text = warning.getvalue()
    assert 'py:class reference target not found: PathLike' not in warnings_text, (
        f'Type alias cross-reference failed in nitpicky mode. Warnings: {warnings_text}'
    )

    # Core functionality test: Verify cross-reference links are generated in the HTML
    html_content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # The type alias should be documented and have an anchor
    assert 'id="alias_module.PathLike"' in html_content, (
        'Type alias definition anchor not found in HTML'
    )

    # The cross-reference to PathLike should be a clickable link
    assert 'href="#alias_module.PathLike"' in html_content, (
        'Type alias cross-reference link not found in HTML'
    )

    # Test the domain resolution mechanism directly
    doctree = app.env.get_doctree('index')

    # Find cross-reference nodes in the doctree
    xref_nodes = list(doctree.findall(addnodes.pending_xref))
    pathlike_xrefs = [
        xref
        for xref in xref_nodes
        if xref.get('reftarget') == 'PathLike' and xref.get('reftype') == 'class'
    ]

    # Should have found the :py:class:`PathLike` cross-reference from index.rst
    assert len(pathlike_xrefs) > 0, (
        'No py:class cross-references to PathLike found in doctree'
    )

    # Test that our Python domain fallback mechanism works
    python_domain = app.env.get_domain('py')

    # Simulate resolving a cross-reference to PathLike as py:class
    # This should work due to our fallback to py:data
    resolved_node = python_domain.resolve_xref(
        app.env,
        'index',
        app.builder,
        'class',
        'alias_module.PathLike',
        pathlike_xrefs[0],
        pathlike_xrefs[0],
    )

    # The key test: cross-reference should resolve successfully
    assert resolved_node is not None, (
        'Type alias cross-reference not resolved - fallback mechanism not working'
    )

    # Verify it resolved to a proper reference node
    assert hasattr(resolved_node, 'tagname'), (
        'Resolved node is not a proper docutils node'
    )
    assert resolved_node.tagname == 'reference', (
        f'Expected reference node, got {resolved_node.tagname}'
    )
