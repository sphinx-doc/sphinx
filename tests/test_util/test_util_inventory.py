"""Test inventory util functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

import sphinx.locale
from sphinx.testing.util import SphinxTestApp
from sphinx.util.inventory import InventoryFile, _InventoryItem

from tests.test_util.intersphinx_data import (
    INVENTORY_V1,
    INVENTORY_V2,
    INVENTORY_V2_AMBIGUOUS_TERMS,
    INVENTORY_V2_NO_VERSION,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_read_inventory_v1() -> None:
    inv = InventoryFile.loads(INVENTORY_V1, uri='/util')
    assert inv['py:module', 'module'] == _InventoryItem(
        project_name='foo',
        project_version='1.0',
        uri='/util/foo.html#module-module',
        display_name='-',
    )
    assert inv['py:class', 'module.cls'] == _InventoryItem(
        project_name='foo',
        project_version='1.0',
        uri='/util/foo.html#module.cls',
        display_name='-',
    )


def test_read_inventory_v2() -> None:
    inv = InventoryFile.loads(INVENTORY_V2, uri='/util')

    assert len(inv.data['py:module']) == 2
    assert inv['py:module', 'module1'] == _InventoryItem(
        project_name='foo',
        project_version='2.0',
        uri='/util/foo.html#module-module1',
        display_name='Long Module desc',
    )
    assert inv['py:module', 'module2'] == _InventoryItem(
        project_name='foo',
        project_version='2.0',
        uri='/util/foo.html#module-module2',
        display_name='-',
    )
    assert inv['py:function', 'module1.func'].uri == ('/util/sub/foo.html#module1.func')
    assert inv['c:function', 'CFunc'].uri == '/util/cfunc.html#CFunc'
    assert inv['std:term', 'a term'].uri == '/util/glossary.html#term-a-term'
    assert inv['std:term', 'a term including:colon'].uri == (
        '/util/glossary.html#term-a-term-including-colon'
    )


def test_read_inventory_v2_not_having_version() -> None:
    inv = InventoryFile.loads(INVENTORY_V2_NO_VERSION, uri='/util')
    assert inv['py:module', 'module1'] == _InventoryItem(
        project_name='foo',
        project_version='',
        uri='/util/foo.html#module-module1',
        display_name='Long Module desc',
    )


@pytest.mark.sphinx('html', testroot='root')
def test_ambiguous_definition_warning(app: SphinxTestApp) -> None:
    InventoryFile.loads(INVENTORY_V2_AMBIGUOUS_TERMS, uri='/util')

    def _multiple_defs_notice_for(entity: str) -> str:
        return f'contains multiple definitions for {entity}'

    # was warning-level; reduced to info-level
    # See: https://github.com/sphinx-doc/sphinx/issues/12613
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
    (dir / prefix).mkdir(parents=True, exist_ok=True)
    (dir / prefix / 'conf.py').write_text(f'language = "{language}"', encoding='utf8')
    (dir / prefix / 'index.rst').write_text('index.rst', encoding='utf8')
    assert sorted(p.name for p in (dir / prefix).iterdir()) == ['conf.py', 'index.rst']
    assert (dir / prefix / 'index.rst').exists()
    return dir / prefix


def _build_inventory(srcdir: Path) -> Path:
    app = SphinxTestApp(srcdir=srcdir)
    app.build()
    sphinx.locale.translators.clear()
    return app.outdir / 'objects.inv'


def test_inventory_localization(tmp_path: Path) -> None:
    # Build an app using Estonian (EE) locale
    srcdir_et = _write_appconfig(tmp_path, 'et')
    inventory_et = _build_inventory(srcdir_et)

    # Build the same app using English (US) locale
    srcdir_en = _write_appconfig(tmp_path, 'en')
    inventory_en = _build_inventory(srcdir_en)

    # Ensure that the inventory contents differ
    assert inventory_et.read_bytes() != inventory_en.read_bytes()
