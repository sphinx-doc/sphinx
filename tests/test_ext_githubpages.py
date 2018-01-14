# -*- coding: utf-8 -*-
"""
    test_ext_githubpages
    ~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.githubpages extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('html', testroot='ext-githubpages')
def test_githubpages(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / '.nojekyll').exists()
