"""Test the BuildInfo class and theme rebuild detection."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.builders.html._build_info import BuildInfo

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from sphinx.testing.util import SphinxTestApp


def test_build_info_theme_hash_is_set(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """BuildInfo should include a theme_hash when a theme is provided."""
    (tmp_path / 'conf.py').touch()
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')
    app = make_app('html', srcdir=tmp_path)
    build_info = app.builder.create_build_info()
    assert build_info.theme_hash != ''


def test_build_info_theme_hash_changes_when_theme_file_changes(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """BuildInfo theme_hash should change when a theme file is modified."""
    (tmp_path / 'conf.py').touch()
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')
    app = make_app('html', srcdir=tmp_path)

    # Get initial theme hash
    build_info_before = app.builder.create_build_info()

    # Modify a theme template file
    theme_dir = app.builder.theme._dirs[0]
    theme_files = list(theme_dir.rglob('*.html'))
    assert theme_files, 'No HTML files found in theme'
    theme_files[0].write_bytes(
        theme_files[0].read_bytes() + b'\n<!-- test change -->'
    )

    # Get new theme hash
    build_info_after = app.builder.create_build_info()

    assert build_info_before.theme_hash != build_info_after.theme_hash
    
def test_build_info_equality_with_same_theme(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """Two BuildInfo objects with same theme should be equal."""
    (tmp_path / 'conf.py').touch()
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')
    app = make_app('html', srcdir=tmp_path)

    build_info_1 = app.builder.create_build_info()
    build_info_2 = app.builder.create_build_info()

    assert build_info_1 == build_info_2


def test_build_info_dump_and_load_preserves_theme_hash(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """theme_hash should survive a dump/load round trip."""
    (tmp_path / 'conf.py').touch()
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')
    app = make_app('html', srcdir=tmp_path)

    build_info = app.builder.create_build_info()
    build_info_path = tmp_path / '.buildinfo'

    # Dump and reload
    build_info.dump(build_info_path)
    loaded = BuildInfo.load(build_info_path)

    assert build_info.theme_hash == loaded.theme_hash


def test_build_info_load_without_theme_hash(tmp_path: Path) -> None:
    """Old .buildinfo files without theme_hash should still load correctly."""
    build_info_path = tmp_path / '.buildinfo'
    build_info_path.write_text(
        '# Sphinx build info version 1\n'
        '# This file records the configuration used when building these files. '
        'When it is not found, a full rebuild will be done.\n'
        'config: abc123\n'
        'tags: def456\n',
        encoding='utf-8',
    )
    loaded = BuildInfo.load(build_info_path)
    assert loaded.config_hash == 'abc123'
    assert loaded.tags_hash == 'def456'
    assert loaded.theme_hash == ''  