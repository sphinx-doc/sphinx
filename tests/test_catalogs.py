# -*- coding: utf-8 -*-
"""
    test_build_base
    ~~~~~~~~~~~~~~~

    Test the base build process.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pytest

from util import find_files


sphinx_intl = pytest.mark.sphinx(
    testroot='intl',
    confoverrides={
        'language': 'en', 'locale_dirs': ['.'],
        'gettext_compact': False,
    },
)


@pytest.fixture
def tmp_app(request, app_params, make_app):
    args, kwargs = app_params
    kwargs['srcdir'] = request.node.name
    app_ = make_app(*args, **kwargs)
    yield app_


@sphinx_intl
@pytest.mark.sphinx('html')
def test_compile_all_catalogs(tmp_app):
    app = tmp_app
    app.builder.compile_all_catalogs()

    catalog_dir = app.srcdir / app.config.language / 'LC_MESSAGES'
    expect = set([
        x.replace('.po', '.mo')
        for x in find_files(catalog_dir, '.po')
    ])
    actual = set(find_files(catalog_dir, '.mo'))
    assert actual  # not empty
    assert actual == expect


@sphinx_intl
@pytest.mark.sphinx('html')
def test_compile_specific_catalogs(tmp_app):
    app = tmp_app
    catalog_dir = app.srcdir / app.config.language / 'LC_MESSAGES'

    def get_actual():
        return set(find_files(catalog_dir, '.mo'))

    actual_on_boot = get_actual()  # sphinx.mo might be included
    app.builder.compile_specific_catalogs(['admonitions'])
    actual = get_actual() - actual_on_boot
    assert actual == {'admonitions.mo'}


@sphinx_intl
@pytest.mark.sphinx('html')
def test_compile_update_catalogs(tmp_app):
    app = tmp_app
    app.builder.compile_update_catalogs()

    catalog_dir = app.srcdir / app.config.language / 'LC_MESSAGES'
    expect = set([
        x.replace('.po', '.mo')
        for x in find_files(catalog_dir, '.po')
    ])
    actual = set(find_files(catalog_dir, '.mo'))
    assert actual  # not empty
    assert actual == expect
