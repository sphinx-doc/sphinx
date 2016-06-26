# -*- coding: utf-8 -*-
"""
    test_util_fileutil
    ~~~~~~~~~~~~~~~~~~

    Tests sphinx.util.fileutil functions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from sphinx.util.fileutil import copy_asset_file
from sphinx.jinja2glue import BuiltinTemplateLoader

from mock import Mock
from util import with_tempdir


class DummyTemplateLoader(BuiltinTemplateLoader):
    def __init__(self):
        BuiltinTemplateLoader.__init__(self)
        builder = Mock()
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
    subdir = (tmpdir / 'subdir')
    subdir.makedirs()

    copy_asset_file(src, subdir, {'var1': 'template'}, renderer)
    assert (subdir / 'asset.txt').exists()
    assert (subdir / 'asset.txt').text() == '# template data'
