# -*- coding: utf-8 -*-
"""
    test_util_fileutil
    ~~~~~~~~~~~~~~~~~~

    Tests sphinx.util.fileutil functions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from sphinx.util.fileutil import copy_asset, copy_asset_file
from sphinx.jinja2glue import BuiltinTemplateLoader

import mock
from util import with_tempdir


class DummyTemplateLoader(BuiltinTemplateLoader):
    def __init__(self):
        BuiltinTemplateLoader.__init__(self)
        builder = mock.Mock()
        builder.config.templates_path = []
        builder.app.translater = None
        self.init(builder)


@with_tempdir
def test_copy_asset_file(tmpdir):
    renderer = DummyTemplateLoader()

    # copy normal file
    src = (tmpdir / 'asset.txt')
    src.write_text('# test data')
    dest = (tmpdir / 'output.txt')

    copy_asset_file(src, dest)
    assert dest.exists()
    assert src.text() == dest.text()

    # copy template file
    src = (tmpdir / 'asset.txt_t')
    src.write_text('# {{var1}} data')
    dest = (tmpdir / 'output.txt_t')

    copy_asset_file(src, dest, {'var1': 'template'}, renderer)
    assert not dest.exists()
    assert (tmpdir / 'output.txt').exists()
    assert (tmpdir / 'output.txt').text() == '# template data'

    # copy template file to subdir
    src = (tmpdir / 'asset.txt_t')
    src.write_text('# {{var1}} data')
    subdir1 = (tmpdir / 'subdir')
    subdir1.makedirs()

    copy_asset_file(src, subdir1, {'var1': 'template'}, renderer)
    assert (subdir1 / 'asset.txt').exists()
    assert (subdir1 / 'asset.txt').text() == '# template data'

    # copy template file without context
    src = (tmpdir / 'asset.txt_t')
    subdir2 = (tmpdir / 'subdir2')
    subdir2.makedirs()

    copy_asset_file(src, subdir2)
    assert not (subdir2 / 'asset.txt').exists()
    assert (subdir2 / 'asset.txt_t').exists()
    assert (subdir2 / 'asset.txt_t').text() == '# {{var1}} data'


@with_tempdir
def test_copy_asset(tmpdir):
    renderer = DummyTemplateLoader()

    # prepare source files
    source = (tmpdir / 'source')
    source.makedirs()
    (source / 'index.rst').write_text('index.rst')
    (source / 'foo.rst_t').write_text('{{var1}}.rst')
    (source / '_static').makedirs()
    (source / '_static' / 'basic.css').write_text('basic.css')
    (source / '_templates').makedirs()
    (source / '_templates' / 'layout.html').write_text('layout.html')
    (source / '_templates' / 'sidebar.html_t').write_text('sidebar: {{var2}}')

    # copy a single file
    assert not (tmpdir / 'test1').exists()
    copy_asset(source / 'index.rst', tmpdir / 'test1')
    assert (tmpdir / 'test1').exists()
    assert (tmpdir / 'test1/index.rst').exists()

    # copy directories
    destdir = tmpdir / 'test2'
    copy_asset(source, destdir, context=dict(var1='bar', var2='baz'), renderer=renderer)
    assert (destdir / 'index.rst').exists()
    assert (destdir / 'foo.rst').exists()
    assert (destdir / 'foo.rst').text() == 'bar.rst'
    assert (destdir / '_static' / 'basic.css').exists()
    assert (destdir / '_templates' / 'layout.html').exists()
    assert (destdir / '_templates' / 'sidebar.html').exists()
    assert (destdir / '_templates' / 'sidebar.html').text() == 'sidebar: baz'

    # copy with exclusion
    def excluded(path):
        return ('sidebar.html' in path or 'basic.css' in path)

    destdir = tmpdir / 'test3'
    copy_asset(source, destdir, excluded,
               context=dict(var1='bar', var2='baz'), renderer=renderer)
    assert (destdir / 'index.rst').exists()
    assert (destdir / 'foo.rst').exists()
    assert not (destdir / '_static' / 'basic.css').exists()
    assert (destdir / '_templates' / 'layout.html').exists()
    assert not (destdir / '_templates' / 'sidebar.html').exists()
