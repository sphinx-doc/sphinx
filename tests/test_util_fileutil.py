"""Tests sphinx.util.fileutil functions."""

from unittest import mock

from sphinx.jinja2glue import BuiltinTemplateLoader
from sphinx.util.fileutil import copy_asset, copy_asset_file


class DummyTemplateLoader(BuiltinTemplateLoader):
    def __init__(self):
        super().__init__()
        builder = mock.Mock()
        builder.config.templates_path = []
        builder.app.translator = None
        self.init(builder)


def test_copy_asset_file(tempdir):
    renderer = DummyTemplateLoader()

    # copy normal file
    src = (tempdir / 'asset.txt')
    src.write_text('# test data')
    dest = (tempdir / 'output.txt')

    copy_asset_file(src, dest)
    assert dest.exists()
    assert src.read_text(encoding='utf8') == dest.read_text(encoding='utf8')

    # copy template file
    src = (tempdir / 'asset.txt_t')
    src.write_text('# {{var1}} data')
    dest = (tempdir / 'output.txt_t')

    copy_asset_file(src, dest, {'var1': 'template'}, renderer)
    assert not dest.exists()
    assert (tempdir / 'output.txt').exists()
    assert (tempdir / 'output.txt').read_text(encoding='utf8') == '# template data'

    # copy template file to subdir
    src = (tempdir / 'asset.txt_t')
    src.write_text('# {{var1}} data')
    subdir1 = (tempdir / 'subdir')
    subdir1.makedirs()

    copy_asset_file(src, subdir1, {'var1': 'template'}, renderer)
    assert (subdir1 / 'asset.txt').exists()
    assert (subdir1 / 'asset.txt').read_text(encoding='utf8') == '# template data'

    # copy template file without context
    src = (tempdir / 'asset.txt_t')
    subdir2 = (tempdir / 'subdir2')
    subdir2.makedirs()

    copy_asset_file(src, subdir2)
    assert not (subdir2 / 'asset.txt').exists()
    assert (subdir2 / 'asset.txt_t').exists()
    assert (subdir2 / 'asset.txt_t').read_text(encoding='utf8') == '# {{var1}} data'


def test_copy_asset(tempdir):
    renderer = DummyTemplateLoader()

    # prepare source files
    source = (tempdir / 'source')
    source.makedirs()
    (source / 'index.rst').write_text('index.rst', encoding='utf8')
    (source / 'foo.rst_t').write_text('{{var1}}.rst', encoding='utf8')
    (source / '_static').makedirs()
    (source / '_static' / 'basic.css').write_text('basic.css', encoding='utf8')
    (source / '_templates').makedirs()
    (source / '_templates' / 'layout.html').write_text('layout.html', encoding='utf8')
    (source / '_templates' / 'sidebar.html_t').write_text('sidebar: {{var2}}', encoding='utf8')

    # copy a single file
    assert not (tempdir / 'test1').exists()
    copy_asset(source / 'index.rst', tempdir / 'test1')
    assert (tempdir / 'test1').exists()
    assert (tempdir / 'test1/index.rst').exists()

    # copy directories
    destdir = tempdir / 'test2'
    copy_asset(source, destdir, context=dict(var1='bar', var2='baz'), renderer=renderer)
    assert (destdir / 'index.rst').exists()
    assert (destdir / 'foo.rst').exists()
    assert (destdir / 'foo.rst').read_text(encoding='utf8') == 'bar.rst'
    assert (destdir / '_static' / 'basic.css').exists()
    assert (destdir / '_templates' / 'layout.html').exists()
    assert (destdir / '_templates' / 'sidebar.html').exists()
    assert (destdir / '_templates' / 'sidebar.html').read_text(encoding='utf8') == 'sidebar: baz'

    # copy with exclusion
    def excluded(path):
        return ('sidebar.html' in path or 'basic.css' in path)

    destdir = tempdir / 'test3'
    copy_asset(source, destdir, excluded,
               context=dict(var1='bar', var2='baz'), renderer=renderer)
    assert (destdir / 'index.rst').exists()
    assert (destdir / 'foo.rst').exists()
    assert not (destdir / '_static' / 'basic.css').exists()
    assert (destdir / '_templates' / 'layout.html').exists()
    assert not (destdir / '_templates' / 'sidebar.html').exists()
