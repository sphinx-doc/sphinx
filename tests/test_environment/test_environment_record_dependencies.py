"""Tests for ``record_dependencies``."""

from __future__ import annotations

import pytest

from sphinx.util._pathlib import _StrPath


@pytest.mark.sphinx('html', testroot='environment-record-dependencies')
def test_record_dependencies_cleared(app) -> None:
    app.builder.read()
    assert 'index' not in app.env.dependencies
    assert app.env.dependencies['api'] == {_StrPath('example_module.py')}
