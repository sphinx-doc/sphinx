# -*- coding: utf-8 -*-
"""
    test_build
    ~~~~~~~~~~

    Test all builders.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pickle
import sys
from textwrap import dedent

import mock
import pytest
from docutils import nodes

from sphinx.errors import SphinxError
from sphinx.testing.path import path


def request_session_head(url, **kwargs):
    response = mock.Mock()
    response.status_code = 200
    response.url = url
    return response


@pytest.fixture
def nonascii_srcdir(request, rootdir, sphinx_test_tempdir):
    # If supported, build in a non-ASCII source dir
    test_name = u'\u65e5\u672c\u8a9e'
    basedir = sphinx_test_tempdir / request.node.originalname
    # Windows with versions prior to 3.2 (I think) doesn't support unicode on system path
    # so we force a non-unicode path in that case
    if (sys.platform == "win32" and
            not (sys.version_info.major >= 3 and sys.version_info.minor >= 2)):
        return basedir / 'all'
    try:
        srcdir = basedir / test_name
        if not srcdir.exists():
            (rootdir / 'test-root').copytree(srcdir)
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
                              """ % {'test_name': test_name}))
    return srcdir


# note: this test skips building docs for some builders because they have independent testcase.
#       (html, epub, latex, texinfo and manpage)
@pytest.mark.parametrize(
    "buildername",
    [
        # note: no 'html' - if it's ok with dirhtml it's ok with html
        'dirhtml', 'singlehtml', 'pickle', 'json', 'text', 'htmlhelp', 'qthelp',
        'applehelp', 'changes', 'xml', 'pseudoxml', 'linkcheck',
    ],
)
@mock.patch('sphinx.builders.linkcheck.requests.head',
            side_effect=request_session_head)
@pytest.mark.xfail(sys.platform == 'win32', reason="Not working on windows")
def test_build_all(requests_head, make_app, nonascii_srcdir, buildername):
    app = make_app(buildername, srcdir=nonascii_srcdir)
    app.build()


def test_master_doc_not_found(tempdir, make_app):
    (tempdir / 'conf.py').write_text('master_doc = "index"')
    assert tempdir.listdir() == ['conf.py']

    app = make_app('dummy', srcdir=tempdir)
    with pytest.raises(SphinxError):
        app.builder.build_all()


@pytest.mark.sphinx(buildername='text', testroot='circular')
def test_circular_toctree(app, status, warning):
    app.builder.build_all()
    warnings = warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- contents <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'contents <- sub <- contents') in warnings


@pytest.mark.sphinx(buildername='text', testroot='numbered-circular')
def test_numbered_circular_toctree(app, status, warning):
    app.builder.build_all()
    warnings = warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- contents <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'contents <- sub <- contents') in warnings


@pytest.mark.sphinx(buildername='dummy', testroot='images')
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
