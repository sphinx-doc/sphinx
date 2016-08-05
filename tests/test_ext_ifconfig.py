# -*- coding: utf-8 -*-
"""
    test_ext_ifconfig
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.ifconfig extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import with_app


@with_app(buildername='text', testroot='ext-ifconfig')
def test_ifconfig(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'index.txt').text()
    assert 'spam' in result
    assert 'ham' not in result
