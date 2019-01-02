# -*- coding: utf-8 -*-
"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~
    Test the HTML Help builder and check output against XPath.
    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest
from six import PY2

from sphinx.builders.htmlhelp import chm_htmlescape


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

    if PY2:
        assert chm_htmlescape('<Hello> "world"') == '&lt;Hello&gt; "world"'
        assert chm_htmlescape('<Hello> "world"', True) == '&lt;Hello&gt; &quot;world&quot;'
        assert chm_htmlescape('<Hello> "world"', False) == '&lt;Hello&gt; "world"'
    else:
        assert chm_htmlescape('<Hello> "world"') == '&lt;Hello&gt; &quot;world&quot;'
        assert chm_htmlescape('<Hello> "world"', True) == '&lt;Hello&gt; &quot;world&quot;'
        assert chm_htmlescape('<Hello> "world"', False) == '&lt;Hello&gt; "world"'

    if PY2:
        # single quotes are not escaped on py2 (following the behavior of cgi.escape())
        assert chm_htmlescape("Hello 'world'") == "Hello 'world'"
        assert chm_htmlescape("Hello 'world'", True) == "Hello 'world'"
        assert chm_htmlescape("Hello 'world'", False) == "Hello 'world'"
    else:
        assert chm_htmlescape("Hello 'world'") == "Hello &#39;world&#39;"
        assert chm_htmlescape("Hello 'world'", True) == "Hello &#39;world&#39;"
        assert chm_htmlescape("Hello 'world'", False) == "Hello 'world'"
