# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import pickle
from docutils import nodes
import pytest
import mock
from textwrap import dedent
from sphinx.errors import SphinxError
import sphinx.builders.linkcheck

from util import rootdir, tempdir, SphinxTestApp, path


def request_session_head(url, **kwargs):
    response = mock.Mock()
    response.status_code = 200
    response.url = url
    return response


@pytest.fixture
def nonascii_srcdir(request):
    # If supported, build in a non-ASCII source dir
    test_name = u'\u65e5\u672c\u8a9e'
    basedir = tempdir / request.node.originalname
    try:
        srcdir = basedir / test_name
        if not srcdir.exists():
            (rootdir / 'root').copytree(srcdir)
    except UnicodeEncodeError:
        srcdir = basedir / 'all'
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
    return srcdir


@pytest.mark.parametrize(
    "buildername",
    [
        # note: no 'html' - if it's ok with dirhtml it's ok with html
        'dirhtml', 'singlehtml', 'latex', 'texinfo', 'pickle', 'json', 'text',
        'htmlhelp', 'qthelp', 'epub2', 'epub', 'applehelp', 'changes', 'xml',
        'pseudoxml', 'man', 'linkcheck',
    ],
)
def test_build_all(make_app, nonascii_srcdir, buildername):
    with mock.patch('sphinx.builders.linkcheck.requests') as requests:
        requests.head = request_session_head
        app = make_app(buildername, srcdir=nonascii_srcdir)
        # if listdir is not empty, we can use built cache
        if not app.outdir.listdir():
            app.build()


def test_master_doc_not_found(tmpdir):
    tmpdir = path(tmpdir)
    (tmpdir / 'conf.py').write_text('master_doc = "index"')
    assert tmpdir.listdir() == ['conf.py']

    try:
        app = SphinxTestApp(buildername='dummy', srcdir=tmpdir)
        app.builder.build_all()
        assert False  # SphinxError not raised
    except Exception as exc:
        assert isinstance(exc, SphinxError)
    finally:
        app.cleanup()


@pytest.mark.sphinx('text', testroot='circular')
def test_circular_toctree(app):
    app.builder.build_all()
    warnings = app.warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- contents <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'contents <- sub <- contents') in warnings


@pytest.mark.sphinx('text', testroot='numbered-circular')
def test_numbered_circular_toctree(app):
    app.builder.build_all()
    warnings = app.warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- contents <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'contents <- sub <- contents') in warnings


@pytest.mark.sphinx('dummy', testroot='image-glob')
def test_image_glob(app):
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
    sub = path('subdir')
    assert doctree[0][1]['candidates'] == {'*': sub / 'rimg.png'}
    assert doctree[0][1]['uri'] == sub / 'rimg.png'

    assert isinstance(doctree[0][2], nodes.image)
    assert doctree[0][2]['candidates'] == {'application/pdf': 'subdir/svgimg.pdf',
                                           'image/svg+xml': 'subdir/svgimg.svg'}
    assert doctree[0][2]['uri'] == sub / 'svgimg.*'

    assert isinstance(doctree[0][3], nodes.figure)
    assert isinstance(doctree[0][3][0], nodes.image)
    assert doctree[0][3][0]['candidates'] == {'application/pdf': 'subdir/svgimg.pdf',
                                              'image/svg+xml': 'subdir/svgimg.svg'}
    assert doctree[0][3][0]['uri'] == sub / 'svgimg.*'
