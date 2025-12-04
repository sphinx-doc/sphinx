"""Tests sphinx.util.fileutil functions."""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

import pytest

from sphinx._cli.util.errors import strip_escape_sequences
from sphinx.jinja2glue import BuiltinTemplateLoader
from sphinx.util.fileutil import _template_basename, copy_asset, copy_asset_file
from sphinx.util.template import BaseRenderer

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


class DummyTemplateLoader(BuiltinTemplateLoader, BaseRenderer):
    def __init__(self) -> None:
        super().__init__()
        builder = mock.Mock()
        builder.config.templates_path = []
        builder._translator = None
        self.init(builder)


def test_copy_asset_file(tmp_path: Path) -> None:
    renderer = DummyTemplateLoader()

    # copy normal file
    src = tmp_path / 'asset.txt'
    src.write_text('# test data', encoding='utf8')
    dest = tmp_path / 'output.txt'

    copy_asset_file(src, dest)
    assert dest.exists()
    assert src.read_text(encoding='utf8') == dest.read_text(encoding='utf8')

    # copy template file
    src = tmp_path / 'asset.txt.jinja'
    src.write_text('# {{var1}} data', encoding='utf8')
    dest = tmp_path / 'output.txt.jinja'

    copy_asset_file(str(src), str(dest), {'var1': 'template'}, renderer)
    assert not dest.exists()
    assert (tmp_path / 'output.txt').exists()
    assert (tmp_path / 'output.txt').read_text(encoding='utf8') == '# template data'

    # copy template file to subdir
    src = tmp_path / 'asset.txt.jinja'
    src.write_text('# {{var1}} data', encoding='utf8')
    subdir1 = tmp_path / 'subdir'
    subdir1.mkdir(parents=True, exist_ok=True)

    copy_asset_file(src, subdir1, context={'var1': 'template'}, renderer=renderer)
    assert (subdir1 / 'asset.txt').exists()
    assert (subdir1 / 'asset.txt').read_text(encoding='utf8') == '# template data'

    # copy template file without context
    src = tmp_path / 'asset.txt.jinja'
    subdir2 = tmp_path / 'subdir2'
    subdir2.mkdir(parents=True, exist_ok=True)

    copy_asset_file(src, subdir2)
    assert not (subdir2 / 'asset.txt').exists()
    assert (subdir2 / 'asset.txt.jinja').exists()
    assert (subdir2 / 'asset.txt.jinja').read_text(encoding='utf8') == '# {{var1}} data'


def test_copy_asset(tmp_path: Path) -> None:
    renderer = DummyTemplateLoader()

    # prepare source files
    source = tmp_path / 'source'
    source.mkdir(parents=True, exist_ok=True)
    (source / 'index.rst').write_text('index.rst', encoding='utf8')
    (source / 'foo.rst.jinja').write_text('{{var1}}.rst', encoding='utf8')
    (source / '_static').mkdir(parents=True, exist_ok=True)
    (source / '_static' / 'basic.css').write_text('basic.css', encoding='utf8')
    (source / '_templates').mkdir(parents=True, exist_ok=True)
    (source / '_templates' / 'layout.html').write_text('layout.html', encoding='utf8')
    (source / '_templates' / 'sidebar.html.jinja').write_text(
        'sidebar: {{var2}}', encoding='utf8'
    )
    sibling = tmp_path / 'sibling'
    sibling.mkdir(parents=True, exist_ok=True)
    sibling.joinpath('spam').mkdir(parents=True, exist_ok=True)
    sibling.joinpath('spam', 'ham').touch()

    # copy a single file
    assert not (tmp_path / 'test1').exists()
    copy_asset(source / 'index.rst', tmp_path / 'test1')
    assert (tmp_path / 'test1').exists()
    assert (tmp_path / 'test1/index.rst').exists()

    # copy directories
    destdir = tmp_path / 'test2'
    copy_asset(
        source,
        destdir,
        context={'var1': 'bar', 'var2': 'baz'},
        renderer=renderer,
    )
    assert (destdir / 'index.rst').exists()
    assert (destdir / 'foo.rst').exists()
    assert (destdir / 'foo.rst').read_text(encoding='utf8') == 'bar.rst'
    assert (destdir / '_static' / 'basic.css').exists()
    assert (destdir / '_templates' / 'layout.html').exists()
    assert (destdir / '_templates' / 'sidebar.html').exists()
    sidebar = (destdir / '_templates' / 'sidebar.html').read_text(encoding='utf8')
    assert sidebar == 'sidebar: baz'

    # copy with exclusion
    def excluded(path: str) -> bool:
        return 'sidebar.html' in path or 'basic.css' in path

    destdir = tmp_path / 'test3'
    copy_asset(
        source,
        destdir,
        excluded,
        context={'var1': 'bar', 'var2': 'baz'},
        renderer=renderer,
    )
    assert (destdir / 'index.rst').exists()
    assert (destdir / 'foo.rst').exists()
    assert not (destdir / '_static' / 'basic.css').exists()
    assert (destdir / '_templates' / 'layout.html').exists()
    assert not (destdir / '_templates' / 'sidebar.html').exists()

    # copy sibling
    assert not (tmp_path / 'test4').exists()
    copy_asset(source / '../sibling', tmp_path / 'test4')
    assert (tmp_path / 'test4').is_dir()
    assert (tmp_path / 'test4' / 'spam').is_dir()
    assert (tmp_path / 'test4' / 'spam' / 'ham').is_file()
    assert (tmp_path / 'test4' / 'spam' / 'ham').read_bytes() == b''


@pytest.mark.sphinx('html', testroot='html_assets')
def test_copy_asset_template(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    expected_msg = r'^Writing evaluated template result to [^\n]*\bAPI.html$'
    output = strip_escape_sequences(app.status.getvalue())
    assert re.findall(expected_msg, output, flags=re.MULTILINE)


@pytest.mark.sphinx('html', testroot='util-copyasset_overwrite')
def test_copy_asset_overwrite(app: SphinxTestApp) -> None:
    app.build()
    src = app.srcdir / 'myext_static' / 'custom-styles.css'
    dst = app.outdir / '_static' / 'custom-styles.css'
    assert strip_escape_sequences(app.warning.getvalue()) == (
        f'WARNING: Aborted attempted copy from {src} to {dst} '
        '(the destination path has existing data). '
        '[misc.copy_overwrite]\n'
    )


def test_template_basename() -> None:
    assert _template_basename(Path('asset.txt')) is None
    assert _template_basename(Path('asset.txt.jinja')) == Path('asset.txt')
    assert _template_basename(Path('sidebar.html.jinja')) == Path('sidebar.html')


def test_legacy_template_basename() -> None:
    assert _template_basename(Path('asset.txt_t')) == Path('asset.txt')
