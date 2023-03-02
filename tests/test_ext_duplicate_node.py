"""Test sphinx.ext.todo extension."""

import pytest

from sphinx.application import Sphinx


@pytest.mark.sphinx('html', testroot='ext-duplicate-node', freshenv=True)
def test_duplicate_node(app: Sphinx) -> None:
    app.warningiserror = True
    app.build()
