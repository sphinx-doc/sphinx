"""Test sphinx.ext.duration extension."""

import re

import pytest


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_githubpages(app):
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3} index\n', app.status.getvalue())
