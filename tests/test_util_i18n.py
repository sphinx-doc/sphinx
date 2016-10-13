# -*- coding: utf-8 -*-
"""
    test_util_i18n
    ~~~~~~~~~~~~~~

    Test i18n util.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import datetime
from os import path

from babel.messages.mofile import read_mo
from sphinx.util import i18n
from sphinx.errors import SphinxError

from util import TestApp, with_tempdir, raises


def test_catalog_info_for_file_and_path():
    cat = i18n.CatalogInfo('path', 'domain', 'utf-8')
    assert cat.po_file == 'domain.po'
    assert cat.mo_file == 'domain.mo'
    assert cat.po_path == path.join('path', 'domain.po')
    assert cat.mo_path == path.join('path', 'domain.mo')


def test_catalog_info_for_sub_domain_file_and_path():
    cat = i18n.CatalogInfo('path', 'sub/domain', 'utf-8')
    assert cat.po_file == 'sub/domain.po'
    assert cat.mo_file == 'sub/domain.mo'
    assert cat.po_path == path.join('path', 'sub/domain.po')
    assert cat.mo_path == path.join('path', 'sub/domain.mo')


@with_tempdir
def test_catalog_outdated(dir):
    (dir / 'test.po').write_text('#')
    cat = i18n.CatalogInfo(dir, 'test', 'utf-8')
    assert cat.is_outdated()  # if mo is not exist

    mo_file = (dir / 'test.mo')
    mo_file.write_text('#')
    assert not cat.is_outdated()  # if mo is exist and newer than po

    os.utime(mo_file, (os.stat(mo_file).st_mtime - 10,) * 2)  # to be outdate
    assert cat.is_outdated()  # if mo is exist and older than po


@with_tempdir
def test_catalog_write_mo(dir):
    (dir / 'test.po').write_text('#')
    cat = i18n.CatalogInfo(dir, 'test', 'utf-8')
    cat.write_mo('en')
    assert path.exists(cat.mo_path)
    with open(cat.mo_path, 'rb') as f:
        assert read_mo(f) is not None


@with_tempdir
def test_get_catalogs_for_xx(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test3.pot').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test5.po').write_text('#')
    (dir / 'loc1' / 'en' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'en' / 'LC_MESSAGES' / 'test6.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_ALL').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_ALL' / 'test7.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], 'xx', force_all=False)
    domains = set(c.domain for c in catalogs)
    assert domains == set([
        'test1',
        'test2',
        'sub/test4',
        'sub/test5',
    ])


@with_tempdir
def test_get_catalogs_for_en(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'xx_dom.po').write_text('#')
    (dir / 'loc1' / 'en' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'en' / 'LC_MESSAGES' / 'en_dom.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], 'en', force_all=False)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['en_dom'])


@with_tempdir
def test_get_catalogs_with_non_existent_locale(dir):
    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], 'xx')
    assert not catalogs

    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], None)
    assert not catalogs


def test_get_catalogs_with_non_existent_locale_dirs():
    catalogs = i18n.find_catalog_source_files(['dummy'], 'xx')
    assert not catalogs


@with_tempdir
def test_get_catalogs_for_xx_without_outdated(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.mo').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.mo').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test3.pot').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test3.mo').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.mo').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test5.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test5.mo').write_text('#')

    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], 'xx', force_all=False)
    assert not catalogs

    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], 'xx', force_all=True)
    domains = set(c.domain for c in catalogs)
    assert domains == set([
        'test1',
        'test2',
        'sub/test4',
        'sub/test5',
    ])


@with_tempdir
def test_get_catalogs_from_multiple_locale_dirs(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc2' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([dir / 'loc1', dir / 'loc2'], 'xx')
    domains = sorted(c.domain for c in catalogs)
    assert domains == ['test1', 'test1', 'test2']


@with_tempdir
def test_get_catalogs_with_compact(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test3.po').write_text('#')
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#')

    catalogs = i18n.find_catalog_source_files([dir / 'loc1'], 'xx', gettext_compact=True)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['test1', 'test2', 'sub'])


def test_format_date():
    date = datetime.date(2016, 2, 7)

    # default format
    format = None
    assert i18n.format_date(format, date=date) == 'Feb 7, 2016'
    assert i18n.format_date(format, date=date, language='') == 'Feb 7, 2016'
    assert i18n.format_date(format, date=date, language='unknown') == 'Feb 7, 2016'
    assert i18n.format_date(format, date=date, language='en') == 'Feb 7, 2016'
    assert i18n.format_date(format, date=date, language='ja') == '2016/02/07'
    assert i18n.format_date(format, date=date, language='de') == '07.02.2016'

    # strftime format
    format = '%B %d, %Y'
    assert i18n.format_date(format, date=date) == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='unknown') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='en') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='ja') == u'2月 07, 2016'
    assert i18n.format_date(format, date=date, language='de') == 'Februar 07, 2016'

    # LDML format
    format = 'MMM dd, YYYY'
    assert i18n.format_date(format, date=date) == 'Feb 07, 2016'
    assert i18n.format_date(format, date=date, language='') == 'Feb 07, 2016'
    assert i18n.format_date(format, date=date, language='unknown') == 'Feb 07, 2016'
    assert i18n.format_date(format, date=date, language='en') == 'Feb 07, 2016'
    assert i18n.format_date(format, date=date, language='ja') == u'2月 07, 2016'
    assert i18n.format_date(format, date=date, language='de') == 'Feb. 07, 2016'

    # raw string
    format = 'Mon Mar 28 12:37:08 2016, commit 4367aef'
    assert i18n.format_date(format, date=date) == format

    format = '%B %d, %Y, %H:%M:%S %I %p'
    datet = datetime.datetime(2016, 2, 7, 5, 11, 17, 0)
    assert i18n.format_date(format, date=datet) == 'February 07, 2016, 05:11:17 05 AM'

    format = '%x'
    assert i18n.format_date(format, date=datet) == 'Feb 7, 2016'
    format = '%X'
    assert i18n.format_date(format, date=datet) == '5:11:17 AM'
    assert i18n.format_date(format, date=date) == 'Feb 7, 2016'
    format = '%c'
    assert i18n.format_date(format, date=datet) == 'Feb 7, 2016, 5:11:17 AM'
    assert i18n.format_date(format, date=date) == 'Feb 7, 2016'


def test_get_filename_for_language():
    app = TestApp()

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
    raises(SphinxError, i18n.get_image_filename_for_language, 'foo.png', app.env)
