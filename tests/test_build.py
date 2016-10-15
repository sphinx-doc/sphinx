# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import BytesIO

import pickle
from docutils import nodes
import mock
from textwrap import dedent
from sphinx.errors import SphinxError
import sphinx.builders.linkcheck

from util import with_app, with_tempdir, rootdir, tempdir, SkipTest, TestApp

try:
    from docutils.writers.manpage import Writer as ManWriter
except ImportError:
    ManWriter = None


def request_session_head(url, **kwargs):
    response = mock.Mock()
    response.status_code = 200
    response.url = url
    return response


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
        master_doc.write_text(master_doc.text() + dedent(u"""
                .. toctree::

                   %(test_name)s/%(test_name)s
                """ % {'test_name': test_name})
        )

    with mock.patch('sphinx.builders.linkcheck.requests') as requests:
        requests.head = request_session_head

        # note: no 'html' - if it's ok with dirhtml it's ok with html
        for buildername in ['dirhtml', 'singlehtml', 'latex', 'texinfo', 'pickle',
                            'json', 'text', 'htmlhelp', 'qthelp', 'epub2', 'epub',
                            'applehelp', 'changes', 'xml', 'pseudoxml', 'man',
                            'linkcheck']:
            yield verify_build, buildername, srcdir


@with_tempdir
def test_master_doc_not_found(tmpdir):
    (tmpdir / 'conf.py').write_text('master_doc = "index"')
    assert tmpdir.listdir() == ['conf.py']

    try:
        app = TestApp(buildername='dummy', srcdir=tmpdir)
        app.builder.build_all()
        assert False  # SphinxError not raised
    except Exception as exc:
        assert isinstance(exc, SphinxError)
    finally:
        app.cleanup()


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


@with_app(buildername='dummy', testroot='image-glob')
def test_image_glob(app, status, warning):
    app.builder.build_all()

    # index.rst
    doctree = pickle.loads((app.doctreedir / 'index.doctree').bytes())

    assert isinstance(doctree[0][1], nodes.image)
    assert doctree[0][1]['candidates'] == {'*': 'rimg.png'}
    assert doctree[0][1]['uri'] == 'rimg.png'

    assert isinstance(doctree[0][2], nodes.figure)
    assert isinstance(doctree[0][2][0], nodes.image)
    assert doctree[0][2][0]['candidates'] == {'*': 'rimg.png'}
    assert doctree[0][2][0]['uri'] == 'rimg.png'

    assert isinstance(doctree[0][3], nodes.image)
    assert doctree[0][3]['candidates'] == {'application/pdf': 'img.pdf',
                                           'image/gif': 'img.gif',
                                           'image/png': 'img.png'}
    assert doctree[0][3]['uri'] == 'img.*'

    assert isinstance(doctree[0][4], nodes.figure)
    assert isinstance(doctree[0][4][0], nodes.image)
    assert doctree[0][4][0]['candidates'] == {'application/pdf': 'img.pdf',
                                              'image/gif': 'img.gif',
                                              'image/png': 'img.png'}
    assert doctree[0][4][0]['uri'] == 'img.*'

    # subdir/index.rst
    doctree = pickle.loads((app.doctreedir / 'subdir/index.doctree').bytes())

    assert isinstance(doctree[0][1], nodes.image)
    assert doctree[0][1]['candidates'] == {'*': 'subdir/rimg.png'}
    assert doctree[0][1]['uri'] == 'subdir/rimg.png'

    assert isinstance(doctree[0][2], nodes.image)
    assert doctree[0][2]['candidates'] == {'application/pdf': 'subdir/svgimg.pdf',
                                           'image/svg+xml': 'subdir/svgimg.svg'}
    assert doctree[0][2]['uri'] == 'subdir/svgimg.*'

    assert isinstance(doctree[0][3], nodes.figure)
    assert isinstance(doctree[0][3][0], nodes.image)
    assert doctree[0][3][0]['candidates'] == {'application/pdf': 'subdir/svgimg.pdf',
                                              'image/svg+xml': 'subdir/svgimg.svg'}
    assert doctree[0][3][0]['uri'] == 'subdir/svgimg.*'
