"""Tests for StandardDomain handling of labels in included files."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='numfig-include')
def test_numref_in_included_file_no_warning(app: SphinxTestApp) -> None:
    """Test that numref works with included files without duplicate label warnings.

    When a file is included via the include directive and also processed as a
    standalone document (not in exclude_patterns), labels should not produce
    duplicate warnings if they come from the same source via include relationship.

    See https://github.com/sphinx-doc/sphinx/issues/14413
    See https://github.com/sphinx-doc/sphinx/issues/9779
    """
    app.build()
    warnings = app.warning.getvalue()

    # Should not have duplicate label warnings for labels in included files
    assert 'duplicate label included-figure' not in warnings
    assert 'duplicate label included-figure-2' not in warnings


@pytest.mark.sphinx('html', testroot='numfig-include', freshenv=True)
def test_numref_in_included_file_correct_numbering(app: SphinxTestApp) -> None:
    """Test that figure numbering is correct when files are included."""
    app.build()

    # Check the output HTML for correct figure numbering
    index_html = (app.outdir / 'index.html').read_text(encoding='utf-8')

    # Figures should be numbered sequentially
    assert 'Fig. 1' in index_html
    assert 'Fig. 2' in index_html
    assert 'Fig. 3' in index_html

    # Numref links should resolve correctly
    assert '<span class="std std-numref">Fig. 1</span>' in index_html
    assert '<span class="std std-numref">Fig. 2</span>' in index_html
    assert '<span class="std std-numref">Fig. 3</span>' in index_html


@pytest.mark.sphinx('html', testroot='numfig-include-duplicate', freshenv=True)
def test_real_duplicate_label_still_warns(app: SphinxTestApp) -> None:
    """Test that real duplicate labels (different source files) still produce warnings.

    When two separate documents (doc1.rst and doc2.rst) both define the same label,
    this is a real duplicate and Sphinx's StandardDomain should warn.
    This ensures we don't over-suppress duplicate warnings.
    """
    app.build()
    warnings = app.warning.getvalue()

    # Should have duplicate label warning because this is a REAL duplicate
    # (label 'shared-label' defined in both doc1.rst AND doc2.rst)
    assert 'duplicate label shared-label' in warnings


@pytest.mark.sphinx('html', testroot='numfig-include', freshenv=True)
def test_incremental_build_no_stale_labels(app: SphinxTestApp, tmp_path: Path) -> None:
    """Test that incremental builds work correctly with included files.

    When a document is rebuilt incrementally, the duplicate detection should
    continue to work properly without false warnings.
    """
    import time

    # Initial build
    app.build()
    warnings = app.warning.getvalue()
    assert 'duplicate label' not in warnings

    # Touch the index file to trigger incremental rebuild
    index_file = app.srcdir / 'index.rst'
    time.sleep(0.1)  # Ensure mtime changes
    index_file.write_text(index_file.read_text(encoding='utf-8'), encoding='utf-8')

    # Clear warnings and rebuild
    app.warning.truncate(0)
    app.warning.seek(0)
    app.build()

    # Should still not have duplicate warnings after incremental rebuild
    warnings = app.warning.getvalue()
    assert 'duplicate label' not in warnings
