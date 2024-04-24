"""Test all builders."""

import os
import shutil
from contextlib import contextmanager
from unittest import mock

import pytest
from docutils import nodes

from sphinx.cmd.build import build_main
from sphinx.errors import SphinxError

from tests.utils import TESTS_ROOT


def request_session_head(url, **kwargs):
    response = mock.Mock()
    response.status_code = 200
    response.url = url
    return response


@pytest.fixture()
def nonascii_srcdir(request, rootdir, sphinx_test_tempdir):
    # Build in a non-ASCII source dir
    test_name = '\u65e5\u672c\u8a9e'
    basedir = sphinx_test_tempdir / request.node.originalname
    srcdir = basedir / test_name
    if not srcdir.exists():
        shutil.copytree(rootdir / 'test-root', srcdir)

    # add a doc with a non-ASCII file name to the source dir
    (srcdir / (test_name + '.txt')).write_text("""
nonascii file name page
=======================
""", encoding='utf8')

    root_doc = srcdir / 'index.txt'
    root_doc.write_text(root_doc.read_text(encoding='utf8') + f"""
.. toctree::

{test_name}/{test_name}
""", encoding='utf8')
    return srcdir


# note: this test skips building docs for some builders because they have independent testcase.
#       (html, changes, epub, latex, texinfo and manpage)
@pytest.mark.parametrize(
    "buildername",
    ['dirhtml', 'singlehtml', 'text', 'xml', 'pseudoxml', 'linkcheck'],
)
@mock.patch('sphinx.builders.linkcheck.requests.head',
            side_effect=request_session_head)
def test_build_all(requests_head, make_app, nonascii_srcdir, buildername):
    app = make_app(buildername, srcdir=nonascii_srcdir)
    app.build()


def test_root_doc_not_found(tmp_path, make_app):
    (tmp_path / 'conf.py').write_text('', encoding='utf8')
    assert os.listdir(tmp_path) == ['conf.py']

    app = make_app('dummy', srcdir=tmp_path)
    with pytest.raises(SphinxError):
        app.build(force_all=True)  # no index.rst


@pytest.mark.sphinx(buildername='text', testroot='circular')
def test_circular_toctree(app, status, warning):
    app.build(force_all=True)
    warnings = warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- index <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'index <- sub <- index') in warnings


@pytest.mark.sphinx(buildername='text', testroot='numbered-circular')
def test_numbered_circular_toctree(app, status, warning):
    app.build(force_all=True)
    warnings = warning.getvalue()
    assert (
        'circular toctree references detected, ignoring: '
        'sub <- index <- sub') in warnings
    assert (
        'circular toctree references detected, ignoring: '
        'index <- sub <- index') in warnings


@pytest.mark.sphinx(buildername='dummy', testroot='images')
def test_image_glob(app, status, warning):
    app.build(force_all=True)

    # index.rst
    doctree = app.env.get_doctree('index')

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
    doctree = app.env.get_doctree('subdir/index')

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


@contextmanager
def force_colors():
    forcecolor = os.environ.get('FORCE_COLOR', None)

    try:
        os.environ['FORCE_COLOR'] = '1'
        yield
    finally:
        if forcecolor is None:
            os.environ.pop('FORCE_COLOR', None)
        else:
            os.environ['FORCE_COLOR'] = forcecolor


def test_log_no_ansi_colors(tmp_path):
    with force_colors():
        wfile = tmp_path / 'warnings.txt'
        srcdir = TESTS_ROOT / 'roots' / 'test-nitpicky-warnings'
        argv = list(map(str, ['-b', 'html', srcdir, tmp_path, '-n', '-w', wfile]))
        retcode = build_main(argv)
        assert retcode == 0

        content = wfile.read_text(encoding='utf8')
        assert '\x1b[91m' not in content
