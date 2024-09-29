"""Test inventory util functions."""

from __future__ import annotations

import os
import posixpath
from io import BytesIO
from typing import TYPE_CHECKING

import pytest

import sphinx.locale
from sphinx.testing.util import SphinxTestApp
from sphinx.util.inventory import InventoryFile

from tests.test_util.intersphinx_data import (
    INVENTORY_V1,
    INVENTORY_V2,
    INVENTORY_V2_AMBIGUOUS_TERMS,
    INVENTORY_V2_NO_VERSION,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_read_inventory_v1():
    f = BytesIO(INVENTORY_V1)
    invdata = InventoryFile.load(f, '/util', posixpath.join)
    assert invdata['py:module']['module'] == (
        'foo',
        '1.0',
        '/util/foo.html#module-module',
        '-',
    )
    assert invdata['py:class']['module.cls'] == (
        'foo',
        '1.0',
        '/util/foo.html#module.cls',
        '-',
    )


def test_read_inventory_v2():
    f = BytesIO(INVENTORY_V2)
    invdata = InventoryFile.load(f, '/util', posixpath.join)

    assert len(invdata['py:module']) == 2
    assert invdata['py:module']['module1'] == (
        'foo',
        '2.0',
        '/util/foo.html#module-module1',
        'Long Module desc',
    )
    assert invdata['py:module']['module2'] == (
        'foo',
        '2.0',
        '/util/foo.html#module-module2',
        '-',
    )
    assert invdata['py:function']['module1.func'][2] == (
        '/util/sub/foo.html#module1.func'
    )
    assert invdata['c:function']['CFunc'][2] == '/util/cfunc.html#CFunc'
    assert invdata['std:term']['a term'][2] == '/util/glossary.html#term-a-term'
    assert invdata['std:term']['a term including:colon'][2] == (
        '/util/glossary.html#term-a-term-including-colon'
    )


def test_read_inventory_v2_not_having_version():
    f = BytesIO(INVENTORY_V2_NO_VERSION)
    invdata = InventoryFile.load(f, '/util', posixpath.join)
    assert invdata['py:module']['module1'] == (
        'foo',
        '',
        '/util/foo.html#module-module1',
        'Long Module desc',
    )


@pytest.mark.sphinx('html', testroot='root')
def test_ambiguous_definition_warning(app):
    f = BytesIO(INVENTORY_V2_AMBIGUOUS_TERMS)
    InventoryFile.load(f, '/util', posixpath.join)

    def _multiple_defs_notice_for(entity: str) -> str:
        return f'contains multiple definitions for {entity}'

    # was warning-level; reduced to info-level - see https://github.com/sphinx-doc/sphinx/issues/12613
    mult_defs_a, mult_defs_b = (
        _multiple_defs_notice_for('std:term:a'),
        _multiple_defs_notice_for('std:term:b'),
    )
    assert mult_defs_a not in app.warning.getvalue().lower()
    assert mult_defs_a not in app.status.getvalue().lower()
    assert mult_defs_b not in app.warning.getvalue().lower()
    assert mult_defs_b in app.status.getvalue().lower()


def _write_appconfig(dir: Path, language: str, prefix: str | None = None) -> Path:
    prefix = prefix or language
    os.makedirs(dir / prefix, exist_ok=True)
    (dir / prefix / 'conf.py').write_text(f'language = "{language}"', encoding='utf8')
    (dir / prefix / 'index.rst').write_text('index.rst', encoding='utf8')
    assert sorted(os.listdir(dir / prefix)) == ['conf.py', 'index.rst']
    assert (dir / prefix / 'index.rst').exists()
    return dir / prefix


def _build_inventory(srcdir: Path) -> Path:
    app = SphinxTestApp(srcdir=srcdir)
    app.build()
    sphinx.locale.translators.clear()
    return app.outdir / 'objects.inv'


def test_inventory_localization(tmp_path):
    # Build an app using Estonian (EE) locale
    srcdir_et = _write_appconfig(tmp_path, 'et')
    inventory_et = _build_inventory(srcdir_et)

    # Build the same app using English (US) locale
    srcdir_en = _write_appconfig(tmp_path, 'en')
    inventory_en = _build_inventory(srcdir_en)

    # Ensure that the inventory contents differ
    assert inventory_et.read_bytes() != inventory_en.read_bytes()
