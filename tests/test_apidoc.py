# -*- coding: utf-8 -*-
"""
    test_apidoc
    ~~~~~~~~~~~

    Test the sphinx.apidoc module.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from __future__ import print_function

import sys

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
