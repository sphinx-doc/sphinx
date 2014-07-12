# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders that have no special checks.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app, test_root, path, SkipTest, TestApp
from textwrap import dedent

try:
    from docutils.writers.manpage import Writer as ManWriter
except ImportError:
    ManWriter = None


builder_names = ['pickle', 'json', 'linkcheck', 'text', 'htmlhelp', 'qthelp',
                 'epub', 'changes', 'singlehtml', 'xml', 'pseudoxml']


def teardown_module():
    (test_root / '_build').rmtree(True)


def test_build():
    for buildername in builder_names:
        app = TestApp(buildername=buildername)
        yield lambda app: app.builder.build_all(), app
        app.cleanup()


@with_app(buildername='man')
def test_man(app):
    if ManWriter is None:
        raise SkipTest('man writer is not available')
    app.builder.build_all()
    assert (app.outdir / 'SphinxTests.1').exists()


@with_app(buildername='html', srcdir='(temp)')
def test_nonascii_path(app):
    srcdir = path(app.srcdir)
    mb_name = u'\u65e5\u672c\u8a9e'
    try:
        (srcdir / mb_name).makedirs()
    except UnicodeEncodeError:
        from path import FILESYSTEMENCODING
        raise SkipTest(
            'nonascii filename not supported on this filesystem encoding: '
            '%s', FILESYSTEMENCODING)

    (srcdir / mb_name / (mb_name + '.txt')).write_text(dedent("""
        multi byte file name page
        ==========================
        """))

    master_doc = srcdir / 'contents.txt'
    master_doc.write_bytes((master_doc.text() + dedent("""
            .. toctree::

               %(mb_name)s/%(mb_name)s
            """ % locals())
    ).encode('utf-8'))
    app.builder.build_all()
