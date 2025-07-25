"""Tests for ``record_dependencies``."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('html', testroot='environment-record-dependencies')
def test_record_dependencies_cleared(app: SphinxTestApp) -> None:
    app.builder.read()
    assert 'index' not in app.env.dependencies
    assert app.env.dependencies['api'] == {app.srcdir / 'example_module.py'}
