"""Tests for ``record_dependencies``."""

import pytest


@pytest.mark.sphinx('html', testroot='environment-record-dependencies')
def test_record_dependencies_cleared(app):
    app.builder.read()
    assert app.env.dependencies['index'] == set()
    assert app.env.dependencies['api'] == {'example_module.py'}
