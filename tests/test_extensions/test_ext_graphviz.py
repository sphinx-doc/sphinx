"""Test sphinx.ext.graphviz extension."""

import re
import sys

import pytest

from sphinx.ext.graphviz import ClickableMapDefinition


@pytest.mark.sphinx('html', testroot='ext-graphviz')
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_png_html(app, status, warning):
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    html = (r'<figure class="align-default" .*?>\s*'
            r'<div class="graphviz"><img .*?/></div>\s*<figcaption>\s*'
            r'<p><span class="caption-text">caption of graph</span>.*</p>\s*'
            r'</figcaption>\s*</figure>')
    assert re.search(html, content, re.S)

    html = 'Hello <div class="graphviz"><img .*?/></div>\n graphviz world'
    assert re.search(html, content, re.S)

    html = ('<img src=".*?" alt="digraph foo {\nbaz -&gt; qux\n}" '
            'class="graphviz neato-graph" />')
    assert re.search(html, content, re.S)

    html = (r'<figure class="align-right" .*?>\s*'
            r'<div class="graphviz"><img .*?/></div>\s*<figcaption>\s*'
            r'<p><span class="caption-text">on <em>right</em></span>.*</p>\s*'
            r'</figcaption>\s*</figure>')
    assert re.search(html, content, re.S)

    html = (r'<div align=\"center\" class=\"align-center\">'
            r'<div class="graphviz"><img src=\".*\.png\" alt=\"digraph foo {\n'
            r'centered\n'
            r'}\" class="graphviz" /></div>\n</div>')
    assert re.search(html, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-graphviz',
                    confoverrides={'graphviz_output_format': 'svg'})
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_svg_html(app, status, warning):
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    html = (r'<figure class=\"align-default\" .*?>\n'
            r'<div class="graphviz"><object data=\".*\.svg\".*>\n'
            r'\s*<p class=\"warning\">digraph foo {\n'
            r'bar -&gt; baz\n'
            r'}</p></object></div>\n'
            r'<figcaption>\n'
            r'<p><span class=\"caption-text\">caption of graph</span>.*</p>\n'
            r'</figcaption>\n'
            r'</figure>')
    assert re.search(html, content, re.S)

    html = (r'Hello <div class="graphviz"><object.*>\n'
            r'\s*<p class=\"warning\">graph</p></object></div>\n'
            r' graphviz world')
    assert re.search(html, content, re.S)

    html = (r'<figure class=\"align-right\" .*\>\n'
            r'<div class="graphviz"><object data=\".*\.svg\".*>\n'
            r'\s*<p class=\"warning\">digraph bar {\n'
            r'foo -&gt; bar\n'
            r'}</p></object></div>\n'
            r'<figcaption>\n'
            r'<p><span class=\"caption-text\">on <em>right</em></span>.*</p>\n'
            r'</figcaption>\n'
            r'</figure>')
    assert re.search(html, content, re.S)

    html = (r'<div align=\"center\" class=\"align-center\">'
            r'<div class="graphviz"><object data=\".*\.svg\".*>\n'
            r'\s*<p class=\"warning\">digraph foo {\n'
            r'centered\n'
            r'}</p></object></div>\n'
            r'</div>')
    assert re.search(html, content, re.S)

    image_re = r'.*data="([^"]+)".*?digraph test'
    image_path_match = re.search(image_re, content, re.S)
    assert image_path_match

    image_path = image_path_match.group(1)
    image_content = (app.outdir / image_path).read_text(encoding='utf8')
    if sys.platform == 'win32':
        assert '".\\_static\\' not in image_content
        assert r'<ns0:image ns1:href="..\_static\images\test.svg"' in image_content
        assert r'<ns0:a ns1:href="..\_static\images\test.svg"' in image_content
    else:
        assert '"./_static/' not in image_content
        assert '<ns0:image ns1:href="../_static/images/test.svg"' in image_content
        assert '<ns0:a ns1:href="../_static/images/test.svg"' in image_content
    assert '<ns0:a ns1:href="..#graphviz"' in image_content


@pytest.mark.sphinx('latex', testroot='ext-graphviz')
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_latex(app, status, warning):
    app.build(force_all=True)

    content = (app.outdir / 'python.tex').read_text(encoding='utf8')
    macro = ('\\\\begin{figure}\\[htbp\\]\n\\\\centering\n\\\\capstart\n\n'
             '\\\\sphinxincludegraphics\\[\\]{graphviz-\\w+.pdf}\n'
             '\\\\caption{caption of graph}\\\\label{.*}\\\\end{figure}')
    assert re.search(macro, content, re.S)

    macro = 'Hello \\\\sphinxincludegraphics\\[\\]{graphviz-\\w+.pdf} graphviz world'
    assert re.search(macro, content, re.S)

    macro = ('\\\\begin{wrapfigure}{r}{0pt}\n\\\\centering\n'
             '\\\\sphinxincludegraphics\\[\\]{graphviz-\\w+.pdf}\n'
             '\\\\caption{on \\\\sphinxstyleemphasis{right}}'
             '\\\\label{.*}\\\\end{wrapfigure}')
    assert re.search(macro, content, re.S)

    macro = (r'\{\\hfill'
             r'\\sphinxincludegraphics\[\]{graphviz-.*}'
             r'\\hspace\*{\\fill}}')
    assert re.search(macro, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-graphviz', confoverrides={'language': 'xx'})
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_i18n(app, status, warning):
    app.build(force_all=True)

    content = (app.outdir / 'index.html').read_text(encoding='utf8')
    html = '<img src=".*?" alt="digraph {\n  BAR -&gt; BAZ\n}" class="graphviz" />'
    assert re.search(html, content, re.M)


def test_graphviz_parse_mapfile():
    # empty graph
    code = ('# digraph {\n'
            '# }\n')
    content = ('<map id="%3" name="%3">\n'
               '</map>')
    cmap = ClickableMapDefinition('dummy.map', content, code)
    assert cmap.filename == 'dummy.map'
    assert cmap.id == 'grapvizb08107169e'
    assert len(cmap.clickable) == 0
    assert cmap.generate_clickable_map() == ''

    # normal graph
    code = ('digraph {\n'
            '  foo [href="https://www.google.com/"];\n'
            '  foo -> bar;\n'
            '}\n')
    content = ('<map id="%3" name="%3">\n'
               '<area shape="poly" id="node1" href="https://www.google.com/" title="foo" alt=""'
               ' coords="77,29,76,22,70,15,62,10,52,7,41,5,30,7,20,10,12,15,7,22,5,29,7,37,12,'
               '43,20,49,30,52,41,53,52,52,62,49,70,43,76,37"/>\n'
               '</map>')
    cmap = ClickableMapDefinition('dummy.map', content, code)
    assert cmap.filename == 'dummy.map'
    assert cmap.id == 'grapvizff087ab863'
    assert len(cmap.clickable) == 1
    assert cmap.generate_clickable_map() == content.replace('%3', cmap.id)

    # inheritance-diagram:: sphinx.builders.html
    content = (
        '<map id="inheritance66ff5471b9" name="inheritance66ff5471b9">\n'
        '<area shape="rect" id="node1" title="Builds target formats from the reST sources."'
        ' alt="" coords="26,95,125,110"/>\n'
        '<area shape="rect" id="node5" title="Builds standalone HTML docs."'
        ' alt="" coords="179,95,362,110"/>\n'
        '<area shape="rect" id="node2" title="buildinfo file manipulator." '
        ' alt="" coords="14,64,138,80"/>\n'
        '<area shape="rect" id="node3" title="The container of stylesheets."'
        ' alt="" coords="3,34,148,49"/>\n'
        '<area shape="rect" id="node4" title="A StandaloneHTMLBuilder that creates all HTML'
        ' pages as &quot;index.html&quot; in" alt="" coords="395,64,569,80"/>\n'
        '<area shape="rect" id="node7" title="An abstract builder that serializes'
        ' the generated HTML." alt="" coords="392,95,571,110"/>\n'
        '<area shape="rect" id="node9" title="A StandaloneHTMLBuilder subclass that puts'
        ' the whole document tree on one" alt="" coords="393,125,570,141"/>\n'
        '<area shape="rect" id="node6" title="A builder that dumps the generated HTML'
        ' into JSON files." alt="" coords="602,80,765,95"/>\n'
        '<area shape="rect" id="node8" title="A Builder that dumps the generated HTML'
        ' into pickle files." alt="" coords="602,110,765,125"/>\n'
        '<area shape="rect" id="node10" title="The metadata of stylesheet."'
        ' alt="" coords="11,3,141,19"/>\n'
        '</map>'
    )
    cmap = ClickableMapDefinition('dummy.map', content, 'dummy_code')
    assert cmap.filename == 'dummy.map'
    assert cmap.id == 'inheritance66ff5471b9'
    assert len(cmap.clickable) == 0
    assert cmap.generate_clickable_map() == ''
