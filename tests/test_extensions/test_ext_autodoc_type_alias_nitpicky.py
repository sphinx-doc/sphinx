"""Test type alias cross-reference resolution in nitpicky mode."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-autodoc-type-alias-xref')
def test_type_alias_xref_resolution(app: SphinxTestApp, warning: Any) -> None:
    """Test that type aliases in function signatures can be cross-referenced."""
    app.build()

    # In nitpicky mode, check that no warnings were generated for type alias cross-references
    warnings_text = warning.getvalue()
    assert 'py:class reference target not found: pathlike' not in warnings_text, (
        f'Type alias cross-reference failed in nitpicky mode. Warnings: {warnings_text}'
    )

    # Core functionality test: Verify type alias links are generated in function signatures
    html_content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # The type alias should be documented and have an anchor
    assert 'id="alias_module.pathlike"' in html_content, (
        'Type alias definition anchor not found in HTML'
    )

    # The critical test: type alias in function signature should be a clickable link
    # This tests the original issue - function signature type annotations should resolve
    assert (
        '<a class="reference internal" href="#alias_module.pathlike"' in html_content
    ), 'Type alias not linked in function signature - this is the core bug'

    # Verify the link is specifically in the function signature context
    import re

    func_sig_match = re.search(
        r'<span class="pre">read_file</span>.*?</dt>', html_content, re.DOTALL
    )
    assert func_sig_match, 'Could not find read_file function signature'
    func_signature = func_sig_match.group(0)
    assert (
        '<a class="reference internal" href="#alias_module.pathlike"' in func_signature
    ), 'Type alias link not found in function signature'
