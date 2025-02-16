"""Test sphinx.ext.duration extension."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_githubpages(app: SphinxTestApp) -> None:
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3} index\n', app.status.getvalue())
