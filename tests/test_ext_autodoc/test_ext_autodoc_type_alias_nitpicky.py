"""Test type alias cross-reference resolution in nitpicky mode."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='ext-autodoc-type-alias-xref')
def test_type_alias_xref_resolution(app: SphinxTestApp) -> None:
    """Test that type aliases in function signatures can be cross-referenced.

    This tests the fix for issue https://github.com/sphinx-doc/sphinx/issues/10785
    where type aliases documented as :py:data: but referenced as :py:class: in
    function signatures would not resolve properly.

    Tests both a Union type alias and a generic type alias to ensure our
    domain fallback mechanism works for various type alias patterns.
    """
    app.build()

    # In nitpicky mode, check that no warnings were generated for type alias cross-references
    warnings_text = app.warning.getvalue()
    assert 'py:class reference target not found: pathlike' not in warnings_text, (
        f'Type alias cross-reference failed in nitpicky mode. Warnings: {warnings_text}'
    )
    assert 'py:class reference target not found: Handler' not in warnings_text, (
        f'Type alias cross-reference failed for Handler. Warnings: {warnings_text}'
    )

    # Core functionality test: Verify type alias links are generated in function signatures
    html_content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # Both type aliases should be documented and have anchors
    assert 'id="alias_module.pathlike"' in html_content, (
        'pathlike type alias definition anchor not found in HTML'
    )
    assert 'id="alias_module.Handler"' in html_content, (
        'Handler type alias definition anchor not found in HTML'
    )

    # The critical test: type aliases in function signatures should be clickable links
    # This tests the original issue - function signature type annotations should resolve
    assert (
        '<a class="reference internal" href="#alias_module.pathlike"' in html_content
    ), 'pathlike type alias not linked in function signature'

    assert (
        '<a class="reference internal" href="#alias_module.Handler"' in html_content
    ), 'Handler type alias not linked in function signature'

    # Verify the links are specifically in the function signature contexts
    # Test pathlike in read_file function signature
    read_file_match = re.search(
        r'<span class="pre">read_file</span>.*?</dt>', html_content, re.DOTALL
    )
    assert read_file_match is not None, 'Could not find read_file function signature'
    read_file_signature = read_file_match.group(0)
    assert (
        '<a class="reference internal" href="#alias_module.pathlike"'
        in read_file_signature
    ), 'pathlike type alias link not found in read_file function signature'

    # Test Handler in process_error function signature
    process_error_match = re.search(
        r'<span class="pre">process_error</span>.*?</dt>', html_content, re.DOTALL
    )
    assert process_error_match is not None, (
        'Could not find process_error function signature'
    )
    process_error_signature = process_error_match.group(0)
    assert (
        '<a class="reference internal" href="#alias_module.Handler"'
        in process_error_signature
    ), 'Handler type alias link not found in process_error function signature'
