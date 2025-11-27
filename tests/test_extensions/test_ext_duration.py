"""Test sphinx.ext.duration extension."""

from __future__ import annotations

import json
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
    freshenv=True,
)
def test_duration(app: SphinxTestApp) -> None:
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    assert re.search('\\d+\\.\\d{3}s index\n', app.status.getvalue())

    assert 'total reading duration' in app.status.getvalue()
    assert 'Total time reading 1 file: ' in app.status.getvalue()
    assert re.search(
        r'Total time reading 1 file: \d+m \d+\.\d{3}s', app.status.getvalue()
    )

    fname = app.outdir / 'sphinx-reading-durations.json'
    assert fname.is_file()

    data = json.loads(fname.read_bytes())
    keys = list(data.keys())
    values = list(data.values())
    assert keys == ['index']
    assert len(values) == 1
    assert isinstance(values[0], float)


@pytest.mark.sphinx(
    'dummy',
    testroot='root',
    confoverrides={'extensions': ['sphinx.ext.duration'], 'duration_n_slowest': 2},
    freshenv=True,
)
def test_n_slowest_value(app: SphinxTestApp) -> None:
    app.build()

    matches = re.findall(r'\d+\.\d{3}s\s+[A-Za-z0-9/]+\n', app.status.getvalue())
    assert len(matches) == 2


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration'], 'duration_n_slowest': 0},
    freshenv=True,
)
def test_n_slowest_all(app: SphinxTestApp) -> None:
    app.build()

    assert 'slowest reading durations' in app.status.getvalue()
    matches = re.findall(r'\d+\.\d{3}s\s+[A-Za-z0-9/]+\n', app.status.getvalue())
    assert len(matches) > 0


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={
        'extensions': ['sphinx.ext.duration'],
        'duration_print_slowest': False,
    },
    freshenv=True,
)
def test_print_slowest_false(app: SphinxTestApp) -> None:
    app.build()

    assert 'slowest reading durations' not in app.status.getvalue()


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={
        'extensions': ['sphinx.ext.duration'],
        'duration_print_total': False,
    },
    freshenv=True,
)
def test_print_total_false(app: SphinxTestApp) -> None:
    app.build()

    assert 'total reading duration' not in app.status.getvalue()


@pytest.mark.parametrize('write_json', [True, False])
@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
    freshenv=True,
)
def test_write_json(app: SphinxTestApp, write_json: bool) -> None:
    if not write_json:
        app.config.duration_write_json = None
    app.build()

    expected = Path(app.outdir) / 'sphinx-reading-durations.json'
    assert expected.is_file() == write_json
    expected.unlink(missing_ok=not write_json)


@pytest.mark.sphinx(
    'dummy',
    testroot='basic',
    confoverrides={'extensions': ['sphinx.ext.duration']},
    freshenv=True,
)
def test_write_json_path(app: SphinxTestApp) -> None:
    parent_name = 'durations'
    file_name = 'durations.json'
    app.config.duration_write_json = str(Path(parent_name, file_name))
    app.build()

    expected_path = app.outdir / parent_name / file_name
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
    app.config.duration_limit = duration_limit
    app.build()

    match = re.search(
        r'index\.rst: WARNING: '
        r'Reading duration \d+\.\d{3}s exceeded the duration limit 0\.000s '
        r'\[duration\]',
        app.warning.getvalue(),
    )
    if expect_warning:
        assert match is not None
    else:
        assert match is None
