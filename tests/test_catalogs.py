# -*- coding: utf-8 -*-
"""
    test_build_base
    ~~~~~~~~~~~~~~~

    Test the base build process.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import shutil

import pytest

from sphinx.testing.util import find_files


@pytest.fixture
def setup_test(app_params):
    srcdir = app_params.kwargs['srcdir']
    locale_dir = srcdir / 'locale'
    # copy all catalogs into locale layout directory
    for po in find_files(srcdir, '.po'):
        copy_po = (locale_dir / 'en' / 'LC_MESSAGES' / po)
        if not copy_po.parent.exists():
            copy_po.parent.makedirs()
        shutil.copy(srcdir / po, copy_po)

    yield

    # delete remnants left over after failed build
    locale_dir.rmtree(True)
    (srcdir / '_build').rmtree(True)


@pytest.mark.usefixtures('setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html', testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']})
def test_compile_all_catalogs(app, status, warning):
    app.builder.compile_all_catalogs()

    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'
    expect = set([
        x.replace('.po', '.mo')
        for x in find_files(catalog_dir, '.po')
    ])
    actual = set(find_files(catalog_dir, '.mo'))
    assert actual  # not empty
    assert actual == expect


@pytest.mark.usefixtures('setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html', testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']})
def test_compile_specific_catalogs(app, status, warning):
    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'

    def get_actual():
        return set(find_files(catalog_dir, '.mo'))

    actual_on_boot = get_actual()  # sphinx.mo might be included
    app.builder.compile_specific_catalogs([app.srcdir / 'admonitions.txt'])
    actual = get_actual() - actual_on_boot
    assert actual == set(['admonitions.mo'])


@pytest.mark.usefixtures('setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html', testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']})
def test_compile_update_catalogs(app, status, warning):
    app.builder.compile_update_catalogs()

    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'
    expect = set([
        x.replace('.po', '.mo')
        for x in find_files(catalog_dir, '.po')
    ])
    actual = set(find_files(catalog_dir, '.mo'))
    assert actual  # not empty
    assert actual == expect
