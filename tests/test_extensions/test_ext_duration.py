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

    assert 'slowest 1 reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3}s index\n', app.status.getvalue())

    assert 'total reading duration' in app.status.getvalue()
    assert 'Total time reading 1 file:' in app.status.getvalue()
    assert re.search(
        r'minutes:\s*\d+\s*seconds:\s*\d+\s*milliseconds:\s*\d+', app.status.getvalue()
    )

    fname = 'sphinx_reading_durations.json'
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
    testroot='root',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_n_slowest_value(app: SphinxTestApp) -> None:
    option = 'duration_n_slowest'
    n_slowest = 2
    app.add_config_value(option, n_slowest, 'env')
    app.build()

    assert f'slowest {n_slowest} reading durations' in app.status.getvalue()
    matches = re.findall(r'\d+\.\d{3}s\s+[A-Za-z0-9]+\n', app.status.getvalue())
    assert len(matches) == n_slowest


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
    freshenv=True,
)
def test_n_slowest_all(app: SphinxTestApp) -> None:
    option = 'duration_n_slowest'
    n_slowest = 0
    app.add_config_value(option, n_slowest, 'env')
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    matches = re.findall(r'\d+\.\d{3}s\s+[A-Za-z0-9]+\n', app.status.getvalue())
    assert len(matches) > n_slowest


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_print_slowest_false(app: SphinxTestApp) -> None:
    option = 'duration_print_slowest'
    print_slowest = False
    app.add_config_value(option, print_slowest, 'env')
    app.build()

    assert 'slowest reading durations' not in app.status.getvalue()


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_print_total_false(app: SphinxTestApp) -> None:
    option = 'duration_print_total'
    print_total = False
    app.add_config_value(option, print_total, 'env')
    app.build()

    assert 'total reading duration' not in app.status.getvalue()


@pytest.mark.parametrize('write_json', [True, False])
@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
)
def test_write_json_false(app: SphinxTestApp, write_json: bool) -> None:
    option = 'duration_write_json'
    app.add_config_value(option, write_json, 'env')
    app.build()

    expected = Path(app.outdir) / 'sphinx_reading_durations.json'
    assert expected.is_file() == write_json
    expected.unlink(missing_ok=not write_json)


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
    freshenv=True,
)
def test_write_json_path(app: SphinxTestApp) -> None:
    option = 'duration_write_json'
    parent_name = 'durations'
    file_name = 'durations.json'
    write_json = str(Path(parent_name) / file_name)
    app.add_config_value(option, write_json, 'env')
    app.build()

    expected_path = Path(app.outdir) / write_json
    assert expected_path.parent.is_dir()
    assert expected_path.is_file()
    assert expected_path.parent.name == parent_name
    assert expected_path.name == file_name


@pytest.mark.parametrize(
    ('duration_limit', 'expect_warning'), [(0.0, True), (1.0, False)]
)
@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
    freshenv=True,
)
def test_duration_limit(
    app: SphinxTestApp, duration_limit: float, expect_warning: bool
) -> None:
    app.add_config_value('duration_limit', duration_limit, 'env')
    app.build()

    match = r'index\.rst: WARNING: Reading duration \d+\.\d{3}s exceeded the duration limit 0\.000s \[duration\]'
    has_warning = re.search(match, app.warning.getvalue()) is not None
    assert has_warning == expect_warning
