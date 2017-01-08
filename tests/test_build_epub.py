# -*- coding: utf-8 -*-
"""
    test_build_html
    ~~~~~~~~~~~~~~~

    Test the HTML builder and check output against XPath.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('epub', testroot='basic')
def test_build_epub(app):
    app.build()
    assert (app.outdir / 'mimetype').text() == 'application/epub+zip'
    assert (app.outdir / 'META-INF' / 'container.xml').exists()
