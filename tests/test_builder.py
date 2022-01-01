"""
    test_builder
    ~~~~~~~~

    Test the Builder class.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest


@pytest.mark.sphinx('dummy', srcdir="test_builder", freshenv=True)
def test_incremental_reading(app):
    # first reading
    updated = app.builder.read()
    assert set(updated) == app.env.found_docs == set(app.env.all_docs)
    assert updated == sorted(updated)  # sorted by alphanumeric

    # test if exclude_patterns works ok
    assert 'subdir/excluded' not in app.env.found_docs

    # before second reading, add, modify and remove source files
    (app.srcdir / 'new.txt').write_text('New file\n========\n')
    app.env.all_docs['index'] = 0  # mark as modified
    (app.srcdir / 'autodoc.txt').unlink()

    # second reading
    updated = app.builder.read()

    assert set(updated) == {'index', 'new'}
    assert 'autodoc' not in app.env.all_docs
    assert 'autodoc' not in app.env.found_docs


@pytest.mark.sphinx('dummy', testroot='warnings', freshenv=True)
def test_incremental_reading_for_missing_files(app):
    # first reading
    updated = app.builder.read()
    assert set(updated) == app.env.found_docs == set(app.env.all_docs)

    # second reading
    updated = app.builder.read()

    # "index" is listed up to updated because it contains references
    # to nonexisting downloadable or image files
    assert set(updated) == {'index'}
