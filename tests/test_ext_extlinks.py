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


@pytest.mark.sphinx("html", testroot="ext-extlinks")
def test_extlinks(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / "index.html").isfile()
    with open(app.outdir / "index.html") as f:
        rst = f.read()

        # simple usage
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

        # callable/advanced usage
        one, two = sys.version_info[0:2]
        assert (
            '<a class="reference external" href="https://docs.python.org/{}.{}/about.html">About</a>'.format(
                one, two
            )
            in rst
        )
