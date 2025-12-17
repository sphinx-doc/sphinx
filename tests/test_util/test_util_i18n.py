"""Test i18n util."""

from __future__ import annotations

import datetime
import os
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from babel.messages.mofile import read_mo

from sphinx.errors import SphinxError
from sphinx.util import i18n

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


def test_catalog_info_for_file_and_path() -> None:
    cat = i18n.CatalogInfo('path', 'domain', 'utf-8')
    assert cat.po_file == 'domain.po'
    assert cat.mo_file == 'domain.mo'
    assert cat.po_path == Path('path', 'domain.po')
    assert cat.mo_path == Path('path', 'domain.mo')


def test_catalog_info_for_sub_domain_file_and_path() -> None:
    cat = i18n.CatalogInfo('path', 'sub/domain', 'utf-8')
    assert cat.po_file == 'sub/domain.po'
    assert cat.mo_file == 'sub/domain.mo'
    assert cat.po_path == Path('path', 'sub', 'domain.po')
    assert cat.mo_path == Path('path', 'sub', 'domain.mo')


def test_catalog_outdated(tmp_path: Path) -> None:
    (tmp_path / 'test.po').write_text('#', encoding='utf8')
    cat = i18n.CatalogInfo(tmp_path, 'test', 'utf-8')
    assert cat.is_outdated()  # if mo is not exist

    mo_file = tmp_path / 'test.mo'
    mo_file.write_text('#', encoding='utf8')
    assert not cat.is_outdated()  # if mo is exist and newer than po

    new_mtime = mo_file.stat().st_mtime_ns - 10_000_000_000
    os.utime(mo_file, ns=(new_mtime, new_mtime))  # to be outdated
    assert cat.is_outdated()  # if mo is exist and older than po


def test_catalog_write_mo(tmp_path: Path) -> None:
    (tmp_path / 'test.po').write_text('#', encoding='utf8')
    cat = i18n.CatalogInfo(tmp_path, 'test', 'utf-8')
    cat.write_mo('en')
    mo_path = Path(cat.mo_path)
    assert mo_path.exists()
    with open(mo_path, 'rb') as f:
        assert read_mo(f) is not None


def test_format_date() -> None:
    date = datetime.datetime(2016, 2, 7, 5, 11, 17, 0)  # NoQA: DTZ001

    # strftime format
    format = '%B %d, %Y'
    assert i18n.format_date(format, date=date, language='') == 'February 07, 2016'
    formatted_unknown = i18n.format_date(format, date=date, language='unknown')
    assert formatted_unknown == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='en') == 'February 07, 2016'
    assert i18n.format_date(format, date=date, language='ja') == '2月 07, 2016'
    assert i18n.format_date(format, date=date, language='de') == 'Februar 07, 2016'

    # raw string
    format = 'Mon Mar 28 12:37:08 2016, commit 4367aef'
    assert i18n.format_date(format, date=date, language='en') == format

    format = '%B %d, %Y, %H:%M:%S %I %p'
    formatted = i18n.format_date(format, date=date, language='en')
    assert formatted == 'February 07, 2016, 05:11:17 05 AM'

    format = '%B %-d, %Y, %-H:%-M:%-S %-I %p'
    formatted = i18n.format_date(format, date=date, language='en')
    assert formatted == 'February 7, 2016, 5:11:17 5 AM'
    format = '%x'
    assert i18n.format_date(format, date=date, language='en') == 'Feb 7, 2016'
    format = '%X'
    assert i18n.format_date(format, date=date, language='en') == '5:11:17\u202fAM'
    format = '%c'
    formatted = i18n.format_date(format, date=date, language='en')
    assert formatted == 'Feb 7, 2016, 5:11:17\u202fAM'

    # timezone
    format = '%Z'
    assert i18n.format_date(format, date=date, language='en') == 'UTC'
    format = '%z'
    assert i18n.format_date(format, date=date, language='en') == '+0000'


def test_format_date_timezone() -> None:
    dt = datetime.datetime(2016, 8, 7, 5, 11, 17, 0, tzinfo=datetime.UTC)
    if time.localtime(dt.timestamp()).tm_gmtoff == 0:
        raise pytest.skip('Local time zone is GMT')  # NoQA: EM101,TRY003

    fmt = '%Y-%m-%d %H:%M:%S'

    iso_gmt = dt.isoformat(' ').split('+')[0]
    fd_gmt = i18n.format_date(fmt, date=dt, language='en', local_time=False)
    assert fd_gmt == '2016-08-07 05:11:17'
    assert fd_gmt == iso_gmt

    iso_local = dt.astimezone().isoformat(' ')[:19]  # strip the timezone
    fd_local = i18n.format_date(fmt, date=dt, language='en', local_time=True)
    assert fd_local == iso_local
    assert fd_local != fd_gmt


@pytest.mark.sphinx('html', testroot='root')
def test_get_filename_for_language(app: SphinxTestApp) -> None:
    get_filename = i18n.get_image_filename_for_language
    app.env.current_document.docname = 'index'

    # language is en
    app.config.language = 'en'
    assert get_filename('foo.png', app.env) == 'foo.en.png'
    assert get_filename('foo.bar.png', app.env) == 'foo.bar.en.png'
    assert get_filename('dir/foo.png', app.env) == 'dir/foo.en.png'
    assert get_filename('../foo.png', app.env) == '../foo.en.png'
    assert get_filename('foo', app.env) == 'foo.en'

    # modify figure_language_filename and language is 'en'
    app.config.language = 'en'
    app.config.figure_language_filename = 'images/{language}/{root}{ext}'
    assert get_filename('foo.png', app.env) == 'images/en/foo.png'
    assert get_filename('foo.bar.png', app.env) == 'images/en/foo.bar.png'
    assert get_filename('subdir/foo.png', app.env) == 'images/en/subdir/foo.png'
    assert get_filename('../foo.png', app.env) == 'images/en/../foo.png'
    assert get_filename('foo', app.env) == 'images/en/foo'

    # new path and basename tokens
    app.config.language = 'en'
    app.config.figure_language_filename = '{path}{language}/{basename}{ext}'
    assert get_filename('foo.png', app.env) == 'en/foo.png'
    assert get_filename('foo.bar.png', app.env) == 'en/foo.bar.png'
    assert get_filename('subdir/foo.png', app.env) == 'subdir/en/foo.png'
    assert get_filename('../foo.png', app.env) == '../en/foo.png'
    assert get_filename('foo', app.env) == 'en/foo'

    # invalid figure_language_filename
    app.config.figure_language_filename = '{root}.{invalid}{ext}'
    with pytest.raises(SphinxError):
        get_filename('foo.png', app.env)

    # docpath (for a document in the top of source directory)
    app.config.language = 'en'
    app.config.figure_language_filename = '/{docpath}{language}/{basename}{ext}'
    assert get_filename('foo.png', app.env) == '/en/foo.png'

    # docpath (for a document in the sub directory)
    app.env.current_document.docname = 'subdir/index'
    assert get_filename('foo.png', app.env) == '/subdir/en/foo.png'


def test_CatalogRepository(tmp_path: Path) -> None:
    for po_file in (
        (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po'),
        (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test2.po'),
        (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test3.po'),
        (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / 'sub' / 'test4.po'),
        (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / '.dotdir' / 'test5.po'),
        (tmp_path / 'loc1' / 'yy' / 'LC_MESSAGES' / 'test6.po'),
        (tmp_path / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test1.po'),
        (tmp_path / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test7.po'),
        (tmp_path / 'loc1' / 'xx' / 'LC_MESSAGES' / '.dotdir2' / 'test8.po'),
    ):
        po_file.parent.mkdir(parents=True, exist_ok=True)
        po_file.write_text('#', encoding='utf8')

    # for language xx
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], 'xx', 'utf-8')
    assert list(repo.locale_dirs) == [
        tmp_path / 'loc1',
        tmp_path / 'loc2',
    ]
    assert all(isinstance(c, i18n.CatalogInfo) for c in repo.catalogs)
    assert sorted(c.domain for c in repo.catalogs) == [
        'sub/test3',
        'sub/test4',
        'test1',
        'test1',
        'test2',
        'test7',
    ]

    # for language yy
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], 'yy', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == ['test6']

    # unknown languages
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], 'zz', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []

    # no languages
    repo = i18n.CatalogRepository(tmp_path, ['loc1', 'loc2'], '', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []

    # unknown locale_dirs
    repo = i18n.CatalogRepository(tmp_path, ['loc3'], '', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []

    # no locale_dirs
    repo = i18n.CatalogRepository(tmp_path, [], '', 'utf-8')
    assert sorted(c.domain for c in repo.catalogs) == []
