# -*- coding: utf-8 -*-
"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~

    Test the HTML Help builder and check output against XPath.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.builders.htmlhelp import default_htmlhelp_basename
from sphinx.config import Config


@pytest.mark.sphinx('htmlhelp', testroot='basic')
def test_default_htmlhelp_file_suffix(app, warning):
    assert app.builder.out_suffix == '.html'


@pytest.mark.sphinx('htmlhelp', testroot='basic',
                    confoverrides={'htmlhelp_file_suffix': '.htm'})
def test_htmlhelp_file_suffix(app, warning):
    assert app.builder.out_suffix == '.htm'


def test_default_htmlhelp_basename():
    config = Config({'project': u'Sphinx Documentation'})
    config.init_values()
    assert default_htmlhelp_basename(config) == 'sphinxdoc'
