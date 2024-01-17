"""Test i18n util."""

import datetime
import os

import babel
import pytest
from babel.messages.mofile import read_mo

from sphinx.errors import SphinxError
from sphinx.util import i18n

BABEL_VERSION = tuple(map(int, babel.__version__.split('.')))


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


def test_catalog_outdated(tmp_path):
    (tmp_path / 'test.po').write_text('#', encoding='utf8')
    cat = i18n.CatalogInfo(tmp_path, 'test', 'utf-8')
    assert cat.is_outdated()  # if mo is not exist

    mo_file = (tmp_path / 'test.mo')
    mo_file.write_text('#', encoding='utf8')
    assert not cat.is_outdated()  # if mo is exist and newer than po

    os.utime(mo_file, (os.stat(mo_file).st_mtime - 10,) * 2)  # to be outdate
    assert cat.is_outdated()  # if mo is exist and older than po


def test_catalog_write_mo(tmp_path):
    (tmp_path / 'test.po').write_text('#', encoding='utf8')
    cat = i18n.CatalogInfo(tmp_path, 'test', 'utf-8')
    cat.write_mo('en')
    assert os.path.exists(cat.mo_path)
    with open(cat.mo_path, 'rb') as f:
        assert read_mo(f) is not None


def test_format_date():
    date = datetime.date(2016, 2, 7)

    # strftime format
    format = '%B %d, %Y'
    assert i18n.format_date(format, date=date, language='') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='unknown') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='en') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='ja') == '2月 07, 2016'
    assert i18n.format_date(format, date=date, language='de') == 'Februar 07, 2016'

    # raw string
    format = 'Mon Mar 28 12:37:08 2016, commit 4367aef'
    assert i18n.format_date(format, date=date, language='en') == format

    format = '%B %d, %Y, %H:%M:%S %I %p'
    datet = datetime.datetime(2016, 2, 7, 5, 11, 17, 0)  # NoQA: DTZ001
    assert i18n.format_date(format, date=datet, language='en') == 'February 07, 2016, 05:11:17 05 AM'

    format = '%B %-d, %Y, %-H:%-M:%-S %-I %p'
    assert i18n.format_date(format, date=datet, language='en') == 'February 7, 2016, 5:11:17 5 AM'
    format = '%x'
    assert i18n.format_date(format, date=datet, language='en') == 'Feb 7, 2016'
    format = '%X'
    if BABEL_VERSION >= (2, 12):
        assert i18n.format_date(format, date=datet, language='en') == '5:11:17\u202fAM'
    else:
        assert i18n.format_date(format, date=datet, language='en') == '5:11:17 AM'
    assert i18n.format_date(format, date=date, language='en') == 'Feb 7, 2016'
    format = '%c'
    if BABEL_VERSION >= (2, 12):
        assert i18n.format_date(format, date=datet, language='en') == 'Feb 7, 2016, 5:11:17\u202fAM'
    else:
        assert i18n.format_date(format, date=datet, language='en') == 'Feb 7, 2016, 5:11:17 AM'
    assert i18n.format_date(format, date=date, language='en') == 'Feb 7, 2016'

    # timezone
    format = '%Z'
    assert i18n.format_date(format, date=datet, language='en') == 'UTC'
    format = '%z'
    assert i18n.format_date(format, date=datet, language='en') == '+0000'


def test_get_filename_for_language(app):
    app.env.temp_data['docname'] = 'index'

    # language is en
    app.env.config.language = 'en'
    assert i18n.get_image_filename_for_language('foo.png', app.env) == 'foo.en.png'
    assert i18n.get_image_filename_for_language('foo.bar.png', app.env) == 'foo.bar.en.png'
    assert i18n.get_image_filename_for_language('dir/foo.png', app.env) == 'dir/foo.en.png'
    assert i18n.get_image_filename_for_language('../foo.png', app.env) == '../foo.en.png'
    assert i18n.get_image_filename_for_language('foo', app.env) == 'foo.en'

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

    # docpath (for a document in the top of source directory)
    app.env.config.language = 'en'
    app.env.config.figure_language_filename = '/{docpath}{language}/{basename}{ext}'
    assert (i18n.get_image_filename_for_language('foo.png', app.env) ==
            '/en/foo.png')

    # docpath (for a document in the sub directory)
    app.env.temp_data['docname'] = 'subdir/index'
    assert (i18n.get_image_filename_for_language('foo.png', app.env) ==
            '/subdir/en/foo.png')


def test_CatalogRepository(tmp_path):
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test3.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / '.dotdir').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / '.dotdir' / 'test5.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc1' / 'yy' / 'LC_MESSAGES').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'loc1' / 'yy' / 'LC_MESSAGES' / 'test6.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc2' / 'xx' / 'LC_MESSAGES').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test7.po').write_text('#', encoding='utf8')
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / '.dotdir2').mkdir(parents=True, exist_ok=True)
    (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / '.dotdir2' / 'test8.po').write_text('#', encoding='utf8')

    # for language xx
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], 'xx', 'utf-8')
    assert list(repo.locale_dirs) == [str(tmp_path / 'loc1'),
                                      str(tmp_path / 'loc2')]
    assert all(isinstance(c, i18n.CatalogInfo) for c in repo.catalogs)
    assert sorted(c.domain for c in repo.catalogs) == ['sub/test3', 'sub/test4',
                                                       'test1', 'test1', 'test2', 'test7']

    # for language yy
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], 'yy', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == ['test6']

    # unknown languages
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], 'zz', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []

    # no languages
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], None, 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []

    # unknown locale_dirs
    repo = i18n.CatalogRepository(tmp_path, ['loc3'], None, 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []

    # no locale_dirs
    repo = i18n.CatalogRepository(tmp_path, [], None, 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []
