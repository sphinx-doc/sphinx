# -*- coding: utf-8 -*-
"""
    test_ext_ifconfig
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.ifconfig extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('text', testroot='ext-ifconfig')
def test_ifconfig(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'index.txt').text()
    assert 'spam' in result
    assert 'ham' not in result
