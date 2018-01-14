# -*- coding: utf-8 -*-
"""
    test_build_qthelp
    ~~~~~~~~~~~~~~~~~

    Test the Qt Help builder and check its output.  We don't need to
    test the HTML itself; that's already handled by
    :file:`test_build_html.py`.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('qthelp', testroot='basic')
def test_qthelp_namespace(app, status, warning):
    # default namespace
    app.builder.build_all()
    qhp = (app.outdir / 'Python.qhp').text()
    assert '<namespace>org.sphinx.python</namespace>' in qhp

    # give a namespace
    app.config.qthelp_namespace = 'org.sphinx-doc.sphinx'
    app.builder.build_all()
    qhp = (app.outdir / 'Python.qhp').text()
    assert '<namespace>org.sphinxdoc.sphinx</namespace>' in qhp
