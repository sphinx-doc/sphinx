"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~

    Test the HTML Help builder and check output against XPath.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest
from html5lib import HTMLParser

from sphinx.builders.htmlhelp import chm_htmlescape, default_htmlhelp_basename
from sphinx.config import Config


@pytest.mark.sphinx('htmlhelp', testroot='basic')
def test_build_htmlhelp(app, status, warning):
    app.build()

    hhp = (app.outdir / 'pythondoc.hhp').text()
    assert 'Compiled file=pythondoc.chm' in hhp
    assert 'Contents file=pythondoc.hhc' in hhp
    assert 'Default Window=pythondoc' in hhp
    assert 'Default topic=index.html' in hhp
    assert 'Full text search stop list file=pythondoc.stp' in hhp
    assert 'Index file=pythondoc.hhk' in hhp
    assert 'Language=0x409' in hhp
    assert 'Title=Python  documentation' in hhp
    assert ('pythondoc="Python  documentation","pythondoc.hhc",'
            '"pythondoc.hhk","index.html","index.html",,,,,'
            '0x63520,220,0x10384e,[0,0,1024,768],,,,,,,0' in hhp)

    files = ['genindex.html', 'index.html', '_static\\alabaster.css', '_static\\basic.css',
             '_static\\custom.css', '_static\\file.png', '_static\\minus.png',
             '_static\\plus.png', '_static\\pygments.css']
    assert '[FILES]\n%s' % '\n'.join(files) in hhp


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


@pytest.mark.sphinx('htmlhelp', testroot='htmlhelp-hhc')
def test_htmlhelp_hhc(app):
    app.build()

    def assert_sitemap(node, name, filename):
        assert node.tag == 'object'
        assert len(node) == 2
        assert node[0].tag == 'param'
        assert node[0].attrib == {'name': 'Name',  'value': name}
        assert node[1].tag == 'param'
        assert node[1].attrib == {'name': 'Local', 'value': filename}

    # .hhc file
    hhc = (app.outdir / 'pythondoc.hhc').text()
    tree = HTMLParser(namespaceHTMLElements=False).parse(hhc)
    items = tree.find('.//body/ul')
    assert len(items) == 4

    # index
    assert items[0].tag == 'li'
    assert len(items[0]) == 1
    assert_sitemap(items[0][0], "Sphinx's documentation", 'index.html')

    # py-modindex
    assert items[1].tag == 'li'
    assert len(items[1]) == 1
    assert_sitemap(items[1][0], 'Python Module Index', 'py-modindex.html')

    # toctree
    assert items[2].tag == 'li'
    assert len(items[2]) == 2
    assert_sitemap(items[2][0], 'foo', 'foo.html')

    assert items[2][1].tag == 'ul'
    assert len(items[2][1]) == 1
    assert items[2][1][0].tag == 'li'
    assert_sitemap(items[2][1][0][0], 'bar', 'bar.html')

    assert items[3].tag == 'li'
    assert len(items[3]) == 1
    assert_sitemap(items[3][0], 'baz', 'baz.html')

    # single quotes should be escaped as decimal (&#39;)
    assert "Sphinx&#39;s documentation" in hhc


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
