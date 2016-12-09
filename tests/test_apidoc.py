# -*- coding: utf-8 -*-
"""
    test_apidoc
    ~~~~~~~~~~~

    Test the sphinx.apidoc module.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import print_function

import sys
from six import PY2

from sphinx import apidoc

from util import with_tempdir, with_app, rootdir


@with_tempdir
def test_simple(tempdir):
    codedir = rootdir / 'root'
    outdir = tempdir / 'out'
    args = ['sphinx-apidoc', '-o', outdir, '-F', codedir]
    apidoc.main(args)

    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'autodoc_fodder.rst').isfile()
    assert (outdir / 'index.rst').isfile()

    @with_app('text', srcdir=outdir)
    def assert_build(app, status, warning):
        app.build()
        print(status.getvalue())
        print(warning.getvalue())

    sys.path.append(codedir)
    try:
        assert_build()
    finally:
        sys.path.remove(codedir)


@with_tempdir
def test_pep_0420_enabled(tempdir):
    codedir = rootdir / 'root' / 'pep_0420'
    outdir = tempdir / 'out'
    args = ['sphinx-apidoc', '-o', outdir, '-F', codedir, "--implicit-namespaces"]
    apidoc.main(args)

    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'a.b.c.rst').isfile()
    assert (outdir / 'a.b.x.rst').isfile()

    with open(outdir / 'a.b.c.rst') as f:
        rst = f.read()
        assert "a.b.c package\n" in rst
        assert "automodule:: a.b.c.d\n" in rst
        assert "automodule:: a.b.c\n" in rst

    with open(outdir / 'a.b.x.rst') as f:
        rst = f.read()
        assert "a.b.x namespace\n" in rst
        assert "automodule:: a.b.x.y\n" in rst
        assert "automodule:: a.b.x\n" not in rst

    @with_app('text', srcdir=outdir)
    def assert_build(app, status, warning):
        app.build()
        print(status.getvalue())
        print(warning.getvalue())

    sys.path.append(codedir)
    try:
        assert_build()
    finally:
        sys.path.remove(codedir)


@with_tempdir
def test_pep_0420_disabled(tempdir):
    codedir = rootdir / 'root' / 'pep_0420'
    outdir = tempdir / 'out'
    args = ['sphinx-apidoc', '-o', outdir, '-F', codedir]
    apidoc.main(args)

    assert (outdir / 'conf.py').isfile()
    assert not (outdir / 'a.b.c.rst').exists()
    assert not (outdir / 'a.b.x.rst').exists()

    @with_app('text', srcdir=outdir)
    def assert_build(app, status, warning):
        app.build()
        print(status.getvalue())
        print(warning.getvalue())

    sys.path.append(codedir)
    try:
        assert_build()
    finally:
        sys.path.remove(codedir)

@with_tempdir
def test_pep_0420_disabled_top_level_verify(tempdir):
    codedir = rootdir / 'root' / 'pep_0420' / 'a' / 'b'
    outdir = tempdir / 'out'
    args = ['sphinx-apidoc', '-o', outdir, '-F', codedir]
    apidoc.main(args)

    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'c.rst').isfile()
    assert not (outdir / 'x.rst').exists()

    with open(outdir / 'c.rst') as f:
        rst = f.read()
        assert "c package\n" in rst
        assert "automodule:: c.d\n" in rst
        assert "automodule:: c\n" in rst

    @with_app('text', srcdir=outdir)
    def assert_build(app, status, warning):
        app.build()
        print(status.getvalue())
        print(warning.getvalue())

    sys.path.append(codedir)
    try:
        assert_build()
    finally:
        sys.path.remove(codedir)

@with_tempdir
def test_multibyte_parameters(tempdir):
    codedir = rootdir / 'root'
    outdir = tempdir / 'out'
    args = ['sphinx-apidoc', '-o', outdir, '-F', codedir,
            '--doc-project', u'プロジェクト名'.encode('utf-8'),
            '--doc-author', u'著者名'.encode('utf-8'),
            '--doc-version', u'バージョン'.encode('utf-8'),
            '--doc-release', u'リリース'.encode('utf-8')]
    apidoc.main(args)

    assert (outdir / 'conf.py').isfile()
    assert (outdir / 'autodoc_fodder.rst').isfile()
    assert (outdir / 'index.rst').isfile()

    conf_py = (outdir / 'conf.py').text()
    if PY2:
        assert u"project = u'プロジェクト名'" in conf_py
        assert u"author = u'著者名'" in conf_py
        assert u"version = u'バージョン'" in conf_py
        assert u"release = u'リリース'" in conf_py
    else:
        assert u"project = 'プロジェクト名'" in conf_py
        assert u"author = '著者名'" in conf_py
        assert u"version = 'バージョン'" in conf_py
        assert u"release = 'リリース'" in conf_py

    @with_app('text', srcdir=outdir)
    def assert_build(app, status, warning):
        app.build()
        print(status.getvalue())
        print(warning.getvalue())

    sys.path.append(codedir)
    try:
        assert_build()
    finally:
        sys.path.remove(codedir)
