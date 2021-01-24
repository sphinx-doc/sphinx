"""
    test_ext_ifconfig
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.ifconfig extension.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('text', testroot='ext-ifconfig')
def test_ifconfig(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'index.txt').read_text()
    assert 'spam' in result
    assert 'ham' not in result
