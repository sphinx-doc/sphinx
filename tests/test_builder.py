# -*- coding: utf-8 -*-
"""
    test_builder
    ~~~~~~~~

    Test the Builder class.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest


@pytest.mark.sphinx('dummy', srcdir="test_builder")
def test_incremental_reading(app):
    # first reading
    updated = app.builder.read()
    assert set(updated) == app.env.found_docs == set(app.env.all_docs)

    # test if exclude_patterns works ok
    assert 'subdir/excluded' not in app.env.found_docs

    # before second reading, add, modify and remove source files
    (app.srcdir / 'new.txt').write_text('New file\n========\n')
    app.env.all_docs['contents'] = 0  # mark as modified
    (app.srcdir / 'autodoc.txt').unlink()

    # second reading
    updated = app.builder.read()

    # "includes" and "images" are in there because they contain references
    # to nonexisting downloadable or image files, which are given another
    # chance to exist
    assert set(updated) == set(['contents', 'new', 'includes', 'images'])
    assert 'autodoc' not in app.env.all_docs
    assert 'autodoc' not in app.env.found_docs


@pytest.mark.sphinx('dummy')
def test_env_read_docs(app):
    """By default, docnames are read in alphanumeric order"""
    def on_env_read_docs_1(app, env, docnames):
        pass

    app.connect('env-before-read-docs', on_env_read_docs_1)

    read_docnames = app.builder.read()
    assert len(read_docnames) > 2 and read_docnames == sorted(read_docnames)

    def on_env_read_docs_2(app, env, docnames):
        docnames.remove('images')

    app.connect('env-before-read-docs', on_env_read_docs_2)

    read_docnames = app.builder.read()
    assert len(read_docnames) == 2
