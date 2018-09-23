# -*- coding: utf-8 -*-
"""
    test_util_i18n
    ~~~~~~~~~~~~~~

    Test i18n util.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import datetime
import os

import pytest
from babel.messages.mofile import read_mo

from sphinx.errors import SphinxError
from sphinx.util import i18n


def test_catalog_info_for_file_and_path():
    cat = i18n.CatalogInfo('path', 'domain', 'utf-8')
    assert cat.po_file == 'domain.po'
    assert cat.mo_file == 'domain.mo'
    assert cat.po_path == os.path.join('path', 'domain.po')
    assert cat.mo_path == os.path.join('path', 'domain.mo')


def test_catalog_info_for_sub_domain_file_and_path():
    cat = i18n.CatalogInfo('path', 'sub/domain', 'utf-8')
    assert cat.po_file == 'sub/domain.po'
    assert cat.mo_file == 'sub/domain.mo'
    assert cat.po_path == os.path.join('path', 'sub/domain.po')
    assert cat.mo_path == os.path.join('path', 'sub/domain.mo')


def test_catalog_outdated(tempdir):
    (tempdir / 'test.po').write_text('#')
    cat = i18n.CatalogInfo(tempdir, 'test', 'utf-8')
    assert cat.is_outdated()  # if mo is not exist

    mo_file = (tempdir / 'test.mo')
    mo_file.write_text('#')
    assert not cat.is_outdated()  # if mo is exist and newer than po

    os.utime(mo_file, (os.stat(mo_file).st_mtime - 10,) * 2)  # to be outdate
    assert cat.is_outdated()  # if mo is exist and older than po


def test_catalog_write_mo(tempdir):
    (tempdir / 'test.po').write_text('#')
    cat = i18n.CatalogInfo(tempdir, 'test', 'utf-8')
    cat.write_mo('en')
    assert os.path.exists(cat.mo_path)
    with open(cat.mo_path, 'rb') as f:
        assert read_mo(f) is not None


def test_get_catalogs_for_xx(tempdir):
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test3.pot').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test5.po').write_text('#')
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES' / 'test6.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_ALL').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_ALL' / 'test7.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], 'xx', force_all=False)
    domains = set(c.domain for c in catalogs)
    assert domains == set([
        'test1',
        'test2',
        'sub/test4',
        'sub/test5',
    ])


def test_get_catalogs_for_en(tempdir):
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'xx_dom.po').write_text('#')
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES' / 'en_dom.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], 'en', force_all=False)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['en_dom'])


def test_get_catalogs_with_non_existent_locale(tempdir):
    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], 'xx')
    assert not catalogs

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], None)
    assert not catalogs


def test_get_catalogs_with_non_existent_locale_dirs():
    catalogs = i18n.find_catalog_source_files(['dummy'], 'xx')
    assert not catalogs


def test_get_catalogs_for_xx_without_outdated(tempdir):
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.mo').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.mo').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test3.pot').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test3.mo').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.mo').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test5.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test5.mo').write_text('#')

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], 'xx', force_all=False)
    assert not catalogs

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], 'xx', force_all=True)
    domains = set(c.domain for c in catalogs)
    assert domains == set([
        'test1',
        'test2',
        'sub/test4',
        'sub/test5',
    ])


def test_get_catalogs_from_multiple_locale_dirs(tempdir):
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (tempdir / 'loc2' / 'xx' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (tempdir / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1', tempdir / 'loc2'], 'xx')
    domains = sorted(c.domain for c in catalogs)
    assert domains == ['test1', 'test1', 'test2']


def test_get_catalogs_with_compact(tempdir):
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').makedirs()
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test3.po').write_text('#')
    (tempdir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([tempdir / 'loc1'], 'xx', gettext_compact=True)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['test1', 'test2', 'sub/test3', 'sub/test4'])


def test_get_catalogs_excluded(tempdir):
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES' / '.git').makedirs()
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES' / 'en_dom.po').write_text('#')
    (tempdir / 'loc1' / 'en' / 'LC_MESSAGES' / '.git' / 'no_no.po').write_text('#')

    catalogs = i18n.find_catalog_source_files(
        [tempdir / 'loc1'], 'en', force_all=False, excluded=lambda path: '.git' in path)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['en_dom'])


def test_format_date():
    date = datetime.date(2016, 2, 7)

    # strftime format
    format = '%B %d, %Y'
    assert i18n.format_date(format, date=date) == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='unknown') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='en') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='ja') == u'2月 07, 2016'
    assert i18n.format_date(format, date=date, language='de') == 'Februar 07, 2016'

    # raw string
    format = 'Mon Mar 28 12:37:08 2016, commit 4367aef'
    assert i18n.format_date(format, date=date) == format

    format = '%B %d, %Y, %H:%M:%S %I %p'
    datet = datetime.datetime(2016, 2, 7, 5, 11, 17, 0)
    assert i18n.format_date(format, date=datet) == 'February 07, 2016, 05:11:17 05 AM'

    format = '%B %-d, %Y, %-H:%-M:%-S %-I %p'
    assert i18n.format_date(format, date=datet) == 'February 7, 2016, 5:11:17 5 AM'
    format = '%x'
    assert i18n.format_date(format, date=datet) == 'Feb 7, 2016'
    format = '%X'
    assert i18n.format_date(format, date=datet) == '5:11:17 AM'
    assert i18n.format_date(format, date=date) == 'Feb 7, 2016'
    format = '%c'
    assert i18n.format_date(format, date=datet) == 'Feb 7, 2016, 5:11:17 AM'
    assert i18n.format_date(format, date=date) == 'Feb 7, 2016'


@pytest.mark.xfail(os.name != 'posix', reason="Path separators don't match on windows")
def test_get_filename_for_language(app):
    # language is None
    app.env.config.language = None
    assert app.env.config.language is None
    assert i18n.get_image_filename_for_language('foo.png', app.env) == 'foo.png'
    assert i18n.get_image_filename_for_language('foo.bar.png', app.env) == 'foo.bar.png'
    assert i18n.get_image_filename_for_language('subdir/foo.png', app.env) == 'subdir/foo.png'
    assert i18n.get_image_filename_for_language('../foo.png', app.env) == '../foo.png'
    assert i18n.get_image_filename_for_language('foo', app.env) == 'foo'

    # language is en
    app.env.config.language = 'en'
    assert i18n.get_image_filename_for_language('foo.png', app.env) == 'foo.en.png'
    assert i18n.get_image_filename_for_language('foo.bar.png', app.env) == 'foo.bar.en.png'
    assert i18n.get_image_filename_for_language('dir/foo.png', app.env) == 'dir/foo.en.png'
    assert i18n.get_image_filename_for_language('../foo.png', app.env) == '../foo.en.png'
    assert i18n.get_image_filename_for_language('foo', app.env) == 'foo.en'

    # modify figure_language_filename and language is None
    app.env.config.language = None
    app.env.config.figure_language_filename = 'images/{language}/{root}{ext}'
    assert i18n.get_image_filename_for_language('foo.png', app.env) == 'foo.png'
    assert i18n.get_image_filename_for_language('foo.bar.png', app.env) == 'foo.bar.png'
    assert i18n.get_image_filename_for_language('subdir/foo.png', app.env) == 'subdir/foo.png'
    assert i18n.get_image_filename_for_language('../foo.png', app.env) == '../foo.png'
    assert i18n.get_image_filename_for_language('foo', app.env) == 'foo'

    # modify figure_language_filename and language is 'en'
    app.env.config.language = 'en'
    app.env.config.figure_language_filename = 'images/{language}/{root}{ext}'
    assert i18n.get_image_filename_for_language('foo.png', app.env) == 'images/en/foo.png'
    assert i18n.get_image_filename_for_language(
        'foo.bar.png', app.env) == 'images/en/foo.bar.png'
    assert i18n.get_image_filename_for_language(
        'subdir/foo.png', app.env) == 'images/en/subdir/foo.png'
    assert i18n.get_image_filename_for_language(
        '../foo.png', app.env) == 'images/en/../foo.png'
    assert i18n.get_image_filename_for_language('foo', app.env) == 'images/en/foo'

    # new path and basename tokens
    app.env.config.language = 'en'
    app.env.config.figure_language_filename = '{path}{language}/{basename}{ext}'
    assert i18n.get_image_filename_for_language('foo.png', app.env) == 'en/foo.png'
    assert i18n.get_image_filename_for_language(
        'foo.bar.png', app.env) == 'en/foo.bar.png'
    assert i18n.get_image_filename_for_language(
        'subdir/foo.png', app.env) == 'subdir/en/foo.png'
    assert i18n.get_image_filename_for_language(
        '../foo.png', app.env) == '../en/foo.png'
    assert i18n.get_image_filename_for_language('foo', app.env) == 'en/foo'

    # invalid figure_language_filename
    app.env.config.figure_language_filename = '{root}.{invalid}{ext}'
    with pytest.raises(SphinxError):
        i18n.get_image_filename_for_language('foo.png', app.env)
