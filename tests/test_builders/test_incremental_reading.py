"""Test the Builder class."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from sphinx.environment import CONFIG_CHANGED, CONFIG_OK

if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.testing.fixtures import _app_params
    from sphinx.testing.util import SphinxTestApp


def _record_read_docnames(app: SphinxTestApp, docnames: list[str]) -> None:
    app.connect(
        'env-before-read-docs',
        lambda _app, _env, names: docnames.extend(names),
    )


def _assert_timestamp_substitutions(app: SphinxTestApp, *, expected_date: str) -> None:
    for docname in ('index', 'second'):
        text = app.env.get_doctree(docname).astext()
        assert f'Sphinx: {expected_date}' in text
        assert f'Docutils: {expected_date}' in text


@pytest.mark.sphinx(
    'dummy',
    testroot='root',
    srcdir='test_builder',
    freshenv=True,
)
def test_incremental_reading(app: SphinxTestApp) -> None:
    # first reading
    updated = app.builder.read()
    assert set(updated) == app.env.found_docs == set(app.env.all_docs)
    assert updated == sorted(updated)  # sorted by alphanumeric

    # test if exclude_patterns works ok
    assert 'subdir/excluded' not in app.env.found_docs

    # before second reading, add, modify and remove source files
    (app.srcdir / 'new.txt').write_text('New file\n========\n', encoding='utf8')
    app.env.all_docs['index'] = 0  # mark as modified
    (app.srcdir / 'autodoc.txt').unlink()

    # second reading
    updated = app.builder.read()

    assert set(updated) == {'index', 'new'}
    assert 'autodoc' not in app.env.all_docs
    assert 'autodoc' not in app.env.found_docs


@pytest.mark.sphinx(
    'dummy',
    testroot='warnings',
    freshenv=True,
)
def test_incremental_reading_for_missing_files(app: SphinxTestApp) -> None:
    # first reading
    updated = app.builder.read()
    assert set(updated) == app.env.found_docs == set(app.env.all_docs)

    # second reading
    updated = app.builder.read()

    # "index" is listed up to updated because it contains references
    # to nonexisting downloadable or image files
    assert set(updated) == {'index'}

    sys.modules.pop('autodoc_fodder', None)


@pytest.mark.sphinx('dummy', testroot='source-date-epoch')
def test_source_date_epoch_invalidates_cached_doctrees(
    make_app: Callable[..., SphinxTestApp],
    app_params: _app_params,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    args, kwargs = app_params
    all_docnames = ['index', 'second']

    monkeypatch.delenv('SOURCE_DATE_EPOCH', raising=False)
    clean_app = make_app(*args, freshenv=True, **kwargs)
    clean_app.build()
    assert clean_app.env._source_date_epoch is None

    # Empty and unset have the same effective value.
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '')
    unchanged_docnames: list[str] = []
    unchanged_app = make_app(*args, **kwargs)
    assert unchanged_app.env.config_status == CONFIG_OK
    _record_read_docnames(unchanged_app, unchanged_docnames)
    unchanged_app.build()
    assert unchanged_docnames == []
    assert unchanged_app.env._source_date_epoch is None

    monkeypatch.setenv('SOURCE_DATE_EPOCH', '0')
    changed_docnames: list[str] = []
    changed_app = make_app(*args, **kwargs)
    assert changed_app.env.config_status == CONFIG_CHANGED
    _record_read_docnames(changed_app, changed_docnames)
    changed_app.build()
    assert changed_docnames == all_docnames
    assert changed_app.env._source_date_epoch == 0
    _assert_timestamp_substitutions(changed_app, expected_date='1970-01-01')

    # Different strings representing the same epoch must not trigger a reread.
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '00')
    unchanged_epoch_docnames: list[str] = []
    unchanged_epoch_app = make_app(*args, **kwargs)
    assert unchanged_epoch_app.env.config_status == CONFIG_OK
    _record_read_docnames(unchanged_epoch_app, unchanged_epoch_docnames)
    unchanged_epoch_app.build()
    assert unchanged_epoch_docnames == []
    assert unchanged_epoch_app.env._source_date_epoch == 0

    # A partial parallel build must still update every cached doctree.
    monkeypatch.setenv('SOURCE_DATE_EPOCH', '86400')
    partial_docnames: list[str] = []
    partial_app = make_app(*args, parallel=2, **kwargs)
    assert partial_app.env.config_status == CONFIG_CHANGED
    _record_read_docnames(partial_app, partial_docnames)
    partial_app.build(filenames=[partial_app.srcdir / 'index.rst'])
    assert partial_docnames == all_docnames
    assert partial_app.env._source_date_epoch == 86400
    _assert_timestamp_substitutions(partial_app, expected_date='1970-01-02')

    monkeypatch.setenv('SOURCE_DATE_EPOCH', '172800')
    forced_docnames: list[str] = []
    forced_app = make_app(*args, **kwargs)
    assert forced_app.env.config_status == CONFIG_CHANGED
    _record_read_docnames(forced_app, forced_docnames)
    forced_app.build(force_all=True)
    assert forced_docnames == all_docnames
    _assert_timestamp_substitutions(forced_app, expected_date='1970-01-03')

    monkeypatch.delenv('SOURCE_DATE_EPOCH')
    unset_docnames: list[str] = []
    unset_app = make_app(*args, **kwargs)
    assert unset_app.env.config_status == CONFIG_CHANGED
    _record_read_docnames(unset_app, unset_docnames)
    unset_app.build()
    assert unset_docnames == all_docnames
    assert unset_app.env._source_date_epoch is None

    monkeypatch.setenv('SOURCE_DATE_EPOCH', '259200')
    fresh_docnames: list[str] = []
    fresh_app = make_app(*args, freshenv=True, **kwargs)
    _record_read_docnames(fresh_app, fresh_docnames)
    fresh_app.build()
    assert fresh_docnames == all_docnames
    assert fresh_app.env._source_date_epoch == 259200
    _assert_timestamp_substitutions(fresh_app, expected_date='1970-01-04')
