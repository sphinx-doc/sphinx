# -*- coding: utf-8 -*-
"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~

    Test the HTML Help builder and check output against XPath.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('htmlhelp', testroot='basic')
def test_default_htmlhelp_file_suffix(app, warning):
    assert app.builder.out_suffix == '.html'


@pytest.mark.sphinx('htmlhelp', testroot='basic',
                    confoverrides={'htmlhelp_file_suffix': '.htm'})
def test_htmlhelp_file_suffix(app, warning):
    assert app.builder.out_suffix == '.htm'
