# -*- coding: utf-8 -*-
"""
    test_build_qthelp_leanid
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Test the Qt Help builder and check its output.  We don't need to
    test the HTML itself; that's already handled by
    :file:`test_build_html.py`. Test for id generation in qhp files

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('qthelp', testroot='index')
def test_qthelp_namespace(app, status, warning):
    # default namespace
    app.builder.build_all()
    qhp = (app.outdir / 'Python.qhp').text()
    assert '<keyword name="features (ID_FEATURE)" id="ID_FEATURE.features"' in qhp

    # give a namespace
    app.config.qthelp_id_lean = True
    app.builder.build_all()
    qhp = (app.outdir / 'Python.qhp').text()
    assert '<keyword name="features" id="ID_FEATURE"' in qhp
