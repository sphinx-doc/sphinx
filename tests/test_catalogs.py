"""Test the base build process."""
import shutil
from pathlib import Path

import pytest

from sphinx.testing.util import find_files


@pytest.fixture()
def _setup_test(app_params):
    assert isinstance(app_params.kwargs['srcdir'], Path)
    srcdir = app_params.kwargs['srcdir']
    src_locale_dir = srcdir / 'xx' / 'LC_MESSAGES'
    dest_locale_dir = srcdir / 'locale'
    # copy all catalogs into locale layout directory
    for po in find_files(src_locale_dir, '.po'):
        copy_po = (dest_locale_dir / 'en' / 'LC_MESSAGES' / po)
        if not copy_po.parent.exists():
            copy_po.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(src_locale_dir / po, copy_po)

    yield

    # delete remnants left over after failed build
    shutil.rmtree(dest_locale_dir, ignore_errors=True)
    shutil.rmtree(srcdir / '_build', ignore_errors=True)


@pytest.mark.usefixtures('_setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html', testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']})
def test_compile_all_catalogs(app, status, warning):
    app.builder.compile_all_catalogs()

    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'
    expect = {x.with_suffix('.mo') for x in find_files(catalog_dir, '.po')}
    actual = set(find_files(catalog_dir, '.mo'))
    assert actual  # not empty
    assert actual == expect


@pytest.mark.usefixtures('_setup_test')
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
    assert set(map(str, actual)) == {'admonitions.mo'}


@pytest.mark.usefixtures('_setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html', testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']})
def test_compile_update_catalogs(app, status, warning):
    app.builder.compile_update_catalogs()

    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'
    expect = {x.with_suffix('.mo') for x in find_files(catalog_dir, '.po')}
    actual = set(find_files(catalog_dir, '.mo'))
    assert actual  # not empty
    assert actual == expect
