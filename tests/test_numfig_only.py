"""Test numfig with only directive."""

from __future__ import annotations

import pytest


@pytest.mark.sphinx('html', testroot='numfig-only', confoverrides={'numfig': True})
def test_numfig_with_only_directive_html(app, status, warning):
    """Test that figure numbers are assigned correctly with only directive in HTML."""
    app.build()

    content = (app.outdir / 'index.html').read_text(encoding='utf-8')

    # In HTML builds, only the HTML figure and common figure should be numbered
    # The HTML figure should be Fig. 1, and common figure should be Fig. 2

    # Check that the HTML figure is numbered as Fig. 1
    assert 'Fig. 1' in content
    # Check that the common figure is numbered as Fig. 2
    assert 'Fig. 2' in content
    # Make sure there's no Fig. 3
    assert 'Fig. 3' not in content


@pytest.mark.sphinx('latex', testroot='numfig-only', confoverrides={'numfig': True})
def test_numfig_with_only_directive_latex(app, status, warning):
    """Test that figure numbers are assigned correctly with only directive in LaTeX.

    Note: This test verifies that figure numbering works correctly with the only directive.
    The actual content filtering (removing HTML-only content from LaTeX output) is handled
    by the OnlyNodeTransform which runs later in the build process.
    """
    app.build(force_all=True)

    content = (
        (app.outdir / 'projectnamenotset.tex')
        .read_text(encoding='utf8')
        .replace('\r\n', '\n')
    )

    # Check that the HTML figure is numbered as Fig. 1
    assert 'Fig. 1' in content
    # Check that the common figure is numbered as Fig. 2
    assert 'Fig. 2' in content
    # Make sure there's no Fig. 3
    assert 'Fig. 3' not in content
