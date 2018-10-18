# -*- coding: utf-8 -*-
"""
    test_ext_extlinks
    ~~~~~~~~~~~

    Test the sphinx.ext.extlinks module.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest
import sys


@pytest.fixture()
def outdir(rootdir, coderoot, tempdir, make_app):
    app = make_app(srcdir=coderoot)
    app.build()
    return app.outdir


@pytest.fixture()
def coderoot(rootdir):
    return rootdir / "test-root"


def test_simple(coderoot, outdir):
    assert (coderoot / "extensions.txt").isfile()
    assert (outdir / "extensions.html").isfile()

    with open(outdir / "extensions.html") as f:
        rst = f.read()
        assert (
            '<a class="reference external" href="http://bugs.python.org/issue1042">explicit caption</a>'
            in rst
        )
        assert (
            '<a class="reference external" href="http://python.org/dev/">http://python.org/dev/</a>'
            in rst
        )
        assert (
            '<a class="reference external" href="http://bugs.python.org/issue1000">issue 1000</a>'
            in rst
        )


def test_callable(coderoot, outdir):
    assert (coderoot / "extensions.txt").isfile()
    assert (outdir / "extensions.html").isfile()

    with open(outdir / "extensions.html") as f:
        rst = f.read()
        assert "about.html" in rst
        one, two = sys.version_info[0:2]
        assert (
            '<a class="reference external" href="https://docs.python.org/{}.{}/about.html">About</a>'.format(
                one, two
            )
            in rst
        )
