# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders that have no special checks.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app, test_root, path
from textwrap import dedent


def teardown_module():
    (test_root / '_build').rmtree(True)

# just let the remaining ones run for now

@with_app(buildername='pickle')
def test_pickle(app):
    app.builder.build_all()

@with_app(buildername='json')
def test_json(app):
    app.builder.build_all()

@with_app(buildername='linkcheck')
def test_linkcheck(app):
    app.builder.build_all()

@with_app(buildername='text')
def test_text(app):
    app.builder.build_all()

@with_app(buildername='htmlhelp')
def test_htmlhelp(app):
    app.builder.build_all()

@with_app(buildername='qthelp')
def test_qthelp(app):
    app.builder.build_all()

@with_app(buildername='epub')
def test_epub(app):
    app.builder.build_all()

@with_app(buildername='changes')
def test_changes(app):
    app.builder.build_all()

try:
    from docutils.writers.manpage import Writer
except ImportError:
    pass
else:
    @with_app(buildername='man')
    def test_man(app):
        app.builder.build_all()
        assert (app.outdir / 'SphinxTests.1').exists()

@with_app(buildername='singlehtml', cleanenv=True)
def test_singlehtml(app):
    app.builder.build_all()

@with_app(buildername='xml')
def test_xml(app):
    app.builder.build_all()

@with_app(buildername='pseudoxml')
def test_pseudoxml(app):
    app.builder.build_all()

@with_app(buildername='html', srcdir='(temp)')
def test_multibyte_path(app):
    srcdir = path(app.srcdir)
    mb_name = u'\u65e5\u672c\u8a9e'
    (srcdir / mb_name).makedirs()
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
