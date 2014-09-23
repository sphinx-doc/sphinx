# -*- coding: utf-8 -*-
"""
    test_util_i18n
    ~~~~~~~~~~~~~~

    Test i18n util.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
from os import path

from babel.messages.mofile import read_mo
from sphinx.util import i18n

from util import with_tempdir


def test_catalog_info_for_file_and_path():
    cat = i18n.CatalogInfo('path', 'domain')
    assert cat.po_file == 'domain.po'
    assert cat.mo_file == 'domain.mo'
    assert cat.po_path == path.join('path', 'domain.po')
    assert cat.mo_path == path.join('path', 'domain.mo')


def test_catalog_info_for_sub_domain_file_and_path():
    cat = i18n.CatalogInfo('path', 'sub/domain')
    assert cat.po_file == 'sub/domain.po'
    assert cat.mo_file == 'sub/domain.mo'
    assert cat.po_path == path.join('path', 'sub/domain.po')
    assert cat.mo_path == path.join('path', 'sub/domain.mo')


@with_tempdir
def test_catalog_outdated(dir):
    (dir / 'test.po').write_text('#')
    cat = i18n.CatalogInfo(dir, 'test')
    assert cat.is_outdated()  # if mo is not exist

    mo_file = (dir / 'test.mo')
    mo_file.write_text('#')
    assert not cat.is_outdated()  # if mo is exist and newer than po

    os.utime(mo_file, (os.stat(mo_file).st_mtime - 10,) * 2) # to be outdate
    assert cat.is_outdated()  # if mo is exist and older than po


@with_tempdir
def test_catalog_write_mo(dir):
    (dir / 'test.po').write_text('#')
    cat = i18n.CatalogInfo(dir, 'test')
    cat.write_mo('en')
    assert path.exists(cat.mo_path)
    assert read_mo(open(cat.mo_path, 'rb')) is not None


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

    catalogs = i18n.get_catalogs([dir / 'loc1'], 'xx', force_all=False)
    domains = set(c.domain for c in catalogs)
    assert domains == set([
        'test1',
        'test2',
        path.normpath('sub/test4'),
        path.normpath('sub/test5'),
    ])


@with_tempdir
def test_get_catalogs_for_en(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'xx_dom.po').write_text('#')
    (dir / 'loc1' / 'en' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'en' / 'LC_MESSAGES' / 'en_dom.po').write_text('#')

    catalogs = i18n.get_catalogs([dir / 'loc1'], 'en', force_all=False)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['en_dom'])


@with_tempdir
def test_get_catalogs_with_non_existent_locale(dir):
    catalogs = i18n.get_catalogs([dir / 'loc1'], 'xx')
    assert not catalogs

    catalogs = i18n.get_catalogs([dir / 'loc1'], None)
    assert not catalogs


def test_get_catalogs_with_non_existent_locale_dirs():
    catalogs = i18n.get_catalogs(['dummy'], 'xx')
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

    catalogs = i18n.get_catalogs([dir / 'loc1'], 'xx', force_all=False)
    assert not catalogs

    catalogs = i18n.get_catalogs([dir / 'loc1'], 'xx', force_all=True)
    domains = set(c.domain for c in catalogs)
    assert domains == set([
        'test1',
        'test2',
        path.normpath('sub/test4'),
        path.normpath('sub/test5'),
    ])


@with_tempdir
def test_get_catalogs_from_multiple_locale_dirs(dir):
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc1' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc2' / 'xx' / 'LC_MESSAGES').makedirs()
    (dir / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test1.po').write_text('#')
    (dir / 'loc2' / 'xx' / 'LC_MESSAGES' / 'test2.po').write_text('#')

    catalogs = i18n.get_catalogs([dir / 'loc1', dir / 'loc2'], 'xx')
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

    catalogs = i18n.get_catalogs([dir / 'loc1'], 'xx', gettext_compact=True)
    domains = set(c.domain for c in catalogs)
    assert domains == set(['test1', 'test2', 'sub'])
