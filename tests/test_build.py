# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import BytesIO

from textwrap import dedent

from util import with_app, rootdir, tempdir, SkipTest, TestApp

try:
    from docutils.writers.manpage import Writer as ManWriter
except ImportError:
    ManWriter = None


class MockOpener(object):
    def open(self, req, **kwargs):
        class result(BytesIO):
            headers = None
            url = req.url
        return result()

import sphinx.builders.linkcheck
sphinx.builders.linkcheck.opener = MockOpener()


def verify_build(buildername, srcdir):
    if buildername == 'man' and ManWriter is None:
        raise SkipTest('man writer is not available')
    app = TestApp(buildername=buildername, srcdir=srcdir)
    try:
        app.builder.build_all()
    finally:
        app.cleanup()


def test_build_all():
    # If supported, build in a non-ASCII source dir
    test_name = u'\u65e5\u672c\u8a9e'
    try:
        srcdir = tempdir / test_name
        (rootdir / 'root').copytree(tempdir / test_name)
    except UnicodeEncodeError:
        srcdir = tempdir / 'all'
    else:
        # add a doc with a non-ASCII file name to the source dir
        (srcdir / (test_name + '.txt')).write_text(dedent("""
            nonascii file name page
            =======================
            """))

        master_doc = srcdir / 'contents.txt'
        master_doc.write_bytes((master_doc.text() + dedent("""
                .. toctree::

                   %(test_name)s/%(test_name)s
                """ % {'test_name': test_name})
        ).encode('utf-8'))

    # note: no 'html' - if it's ok with dirhtml it's ok with html
    for buildername in ['dirhtml', 'singlehtml', 'latex', 'texinfo',
                        'pickle', 'json', 'text', 'htmlhelp', 'qthelp', 'epub',
                        'changes', 'xml', 'pseudoxml', 'man', 'linkcheck']:
        yield verify_build, buildername, srcdir


@with_app(buildername='text', testroot='circular')
def test_circular_toctree(app, status, warning):
    app.builder.build_all()
    warnings = warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- contents <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'contents <- sub <- contents') in warnings


@with_app(buildername='text', testroot='numbered-circular')
def test_numbered_circular_toctree(app, status, warning):
    app.builder.build_all()
    warnings = warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- contents <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'contents <- sub <- contents') in warnings
