"""Test sphinx.ext.duration extension."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_duration(app: SphinxTestApp) -> None:
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3} index\n', app.status.getvalue())

    assert 'total reading duration' in app.status.getvalue()
    assert 'Total time reading 1 file:' in app.status.getvalue()
    assert re.search(
        r'minutes:\s*\d+\s*seconds:\s*\d+\s*milliseconds:\s*\d+', app.status.getvalue()
    )

    fname = 'sphinx_durations.json'
    assert fname in os.listdir(app.outdir)  # noqa: PTH208
    with (Path(app.outdir) / fname).open() as f:
        data = json.load(f)

    keys = list(data.keys())
    values = list(data.values())
    assert keys == ['index']
    assert len(values) == 1
    assert isinstance(values[0], float)


@pytest.mark.sphinx(
    'dummy',
    testroot='intl',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_n_slowest_value(app: SphinxTestApp) -> None:
    options = {'n_slowest': 0}
    app.add_config_value('duration_options', options, 'env')
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3} index\n', app.status.getvalue()) is None


@pytest.mark.sphinx(
    'dummy',
    testroot='root',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_n_slowest_all(app: SphinxTestApp) -> None:
    options = {'n_slowest': -1}
    app.add_config_value('duration_options', options, 'env')
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3} index\n', app.status.getvalue())


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_print_slowest_false(app: SphinxTestApp) -> None:
    options = {'print_slowest': False}
    app.add_config_value('duration_options', options, 'env')
    app.build()

    assert 'slowest reading durations' not in app.status.getvalue()


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_print_total_false(app: SphinxTestApp) -> None:
    options = {'print_total': False}
    app.add_config_value('duration_options', options, 'env')
    app.build()

    assert 'total reading duration' not in app.status.getvalue()


@pytest.mark.sphinx(
    'dummy',
    testroot='search',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_write_durations_false(app: SphinxTestApp) -> None:
    options = {'write_durations': False}
    app.add_config_value('duration_options', options, 'env')
    app.build()

    assert 'sphinx_durations.json' not in os.listdir(app.outdir)  # noqa: PTH208
