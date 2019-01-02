"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~

    Test the HTML Help builder and check output against XPath.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest

from sphinx.builders.htmlhelp import chm_htmlescape

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
    config = Config({'project': 'Sphinx Documentation'})
    config.init_values()
    assert default_htmlhelp_basename(config) == 'sphinxdoc'


@pytest.mark.sphinx('htmlhelp', testroot='build-htmlhelp')
def test_chm(app):
    app.build()

    # check .hhk file
    outname = app.builder.config.htmlhelp_basename
    hhk_path = str(app.outdir / outname + '.hhk')

    with open(hhk_path, 'rb') as f:
        data = f.read()
    m = re.search(br'&#[xX][0-9a-fA-F]+;', data)
    assert m is None, 'Hex escaping exists in .hhk file: ' + str(m.group(0))


def test_chm_htmlescape():
    assert chm_htmlescape('Hello world') == 'Hello world'
    assert chm_htmlescape(u'Unicode 文字') == u'Unicode 文字'
    assert chm_htmlescape('&#x45') == '&amp;#x45'

    assert chm_htmlescape('<Hello> "world"') == '&lt;Hello&gt; &quot;world&quot;'
    assert chm_htmlescape('<Hello> "world"', True) == '&lt;Hello&gt; &quot;world&quot;'
    assert chm_htmlescape('<Hello> "world"', False) == '&lt;Hello&gt; "world"'

    assert chm_htmlescape("Hello 'world'") == "Hello &#39;world&#39;"
    assert chm_htmlescape("Hello 'world'", True) == "Hello &#39;world&#39;"
    assert chm_htmlescape("Hello 'world'", False) == "Hello 'world'"
