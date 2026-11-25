"""Test the BuildInfo class and theme rebuild detection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.builders.html import StandaloneHTMLBuilder
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
    builder = app.builder
    assert isinstance(builder, StandaloneHTMLBuilder)

    build_info = builder.create_build_info()
    assert build_info.theme_hash != ''


def test_build_info_theme_hash_changes_when_theme_file_changes(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """BuildInfo theme_hash should change when a theme file is modified."""
    # Use a project-local theme, so the test never modifies a theme
    # shipped with Sphinx (other tests may be reading it in parallel).
    theme_dir = tmp_path / '_themes' / 'local'
    theme_dir.mkdir(parents=True)
    (theme_dir / 'theme.toml').write_text(
        '[theme]\ninherit = "basic"\n', encoding='utf-8'
    )
    layout = theme_dir / 'layout.html'
    layout.write_text('{% extends "basic/layout.html" %}\n', encoding='utf-8')
    (tmp_path / 'conf.py').write_text(
        "html_theme = 'local'\nhtml_theme_path = ['_themes']\n", encoding='utf-8'
    )
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')

    app = make_app('html', srcdir=tmp_path)
    builder = app.builder
    assert isinstance(builder, StandaloneHTMLBuilder)
    assert builder.theme._dirs[0] == theme_dir

    # Get initial theme hash
    build_info_before = builder.create_build_info()

    # Modify the local theme's template
    layout.write_text(
        layout.read_text(encoding='utf-8') + '<!-- test change -->\n', encoding='utf-8'
    )

    # Get new theme hash
    build_info_after = builder.create_build_info()

    assert build_info_before.theme_hash != build_info_after.theme_hash


def test_build_info_equality_with_same_theme(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """Two BuildInfo objects with same theme should be equal."""
    (tmp_path / 'conf.py').touch()
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')

    app = make_app('html', srcdir=tmp_path)
    builder = app.builder
    assert isinstance(builder, StandaloneHTMLBuilder)

    build_info_1 = builder.create_build_info()
    build_info_2 = builder.create_build_info()

    assert build_info_1 == build_info_2


def test_build_info_dump_and_load_preserves_theme_hash(
    make_app: Callable[..., SphinxTestApp], tmp_path: Path
) -> None:
    """theme_hash should survive a dump/load round trip."""
    (tmp_path / 'conf.py').touch()
    (tmp_path / 'index.rst').write_text('Test\n====\n', encoding='utf-8')

    app = make_app('html', srcdir=tmp_path)
    builder = app.builder
    assert isinstance(builder, StandaloneHTMLBuilder)

    build_info = builder.create_build_info()
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
