"""Test the base build process."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sphinx.testing.fixtures import _app_params
    from sphinx.testing.util import SphinxTestApp


@pytest.fixture
def _setup_test(app_params: _app_params) -> Iterator[None]:
    assert isinstance(app_params.kwargs['srcdir'], Path)
    srcdir = app_params.kwargs['srcdir']
    src_locale_dir = srcdir / 'xx' / 'LC_MESSAGES'
    dest_locale_dir = srcdir / 'locale'
    # copy all catalogs into locale layout directory
    for po in src_locale_dir.rglob('*.po'):
        copy_po = (
            dest_locale_dir / 'en' / 'LC_MESSAGES' / po.relative_to(src_locale_dir)
        )
        if not copy_po.parent.exists():
            copy_po.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(po, copy_po)

    yield

    # delete remnants left over after failed build
    shutil.rmtree(dest_locale_dir, ignore_errors=True)
    shutil.rmtree(srcdir / '_build', ignore_errors=True)


@pytest.mark.usefixtures('_setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html',
    testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']},
)
def test_compile_all_catalogs(app: SphinxTestApp) -> None:
    app.builder.compile_all_catalogs()

    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'
    expect = {x.with_suffix('.mo') for x in catalog_dir.rglob('*.po')}
    actual = set(catalog_dir.rglob('*.mo'))
    assert actual  # not empty
    assert actual == expect


@pytest.mark.usefixtures('_setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html',
    testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']},
)
def test_compile_specific_catalogs(app: SphinxTestApp) -> None:
    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'

    actual_on_boot = set(catalog_dir.rglob('*.mo'))  # sphinx.mo might be included
    app.builder.compile_specific_catalogs([app.srcdir / 'admonitions.txt'])
    actual = {
        str(x.relative_to(catalog_dir))
        for x in catalog_dir.rglob('*.mo')
        if x not in actual_on_boot
    }
    assert actual == {'admonitions.mo'}


@pytest.mark.usefixtures('_setup_test')
@pytest.mark.test_params(shared_result='test-catalogs')
@pytest.mark.sphinx(
    'html',
    testroot='intl',
    confoverrides={'language': 'en', 'locale_dirs': ['./locale']},
)
def test_compile_update_catalogs(app: SphinxTestApp) -> None:
    app.builder.compile_update_catalogs()

    locale_dir = app.srcdir / 'locale'
    catalog_dir = locale_dir / app.config.language / 'LC_MESSAGES'
    expect = {x.with_suffix('.mo') for x in set(catalog_dir.rglob('*.po'))}
    actual = set(catalog_dir.rglob('*.mo'))
    assert actual  # not empty
    assert actual == expect
