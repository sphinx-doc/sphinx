"""
    test_ext_graphviz
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.graphviz extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest

from sphinx.ext.graphviz import ClickableMapDefinition
from sphinx.util import docutils


@pytest.mark.sphinx('html', testroot='ext-graphviz')
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_png_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
    if docutils.__version_info__ < (0, 17):
        html = (r'<div class="figure align-default" .*?>\s*'
                r'<div class="graphviz"><img .*?/></div>\s*<p class="caption">'
                r'<span class="caption-text">caption of graph</span>.*</p>\s*</div>')
    else:
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

    if docutils.__version_info__ < (0, 17):
        html = (r'<div class="figure align-right" .*?>\s*'
                r'<div class="graphviz"><img .*?/></div>\s*<p class="caption">'
                r'<span class="caption-text">on <em>right</em></span>.*</p>\s*</div>')
    else:
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
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()

    if docutils.__version_info__ < (0, 17):
        html = (r'<div class=\"figure align-default\" .*?>\n'
                r'<div class="graphviz"><object data=\".*\.svg\".*>\n'
                r'\s*<p class=\"warning\">digraph foo {\n'
                r'bar -&gt; baz\n'
                r'}</p></object></div>\n'
                r'<p class=\"caption\"><span class=\"caption-text\">'
                r'caption of graph</span>.*</p>\n</div>')
    else:
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

    if docutils.__version_info__ < (0, 17):
        html = (r'<div class=\"figure align-right\" .*\>\n'
                r'<div class="graphviz"><object data=\".*\.svg\".*>\n'
                r'\s*<p class=\"warning\">digraph bar {\n'
                r'foo -&gt; bar\n'
                r'}</p></object></div>\n'
                r'<p class=\"caption\"><span class=\"caption-text\">'
                r'on <em>right</em></span>.*</p>\n'
                r'</div>')
    else:
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


@pytest.mark.sphinx('latex', testroot='ext-graphviz')
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'python.tex').read_text()
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
    app.builder.build_all()

    content = (app.outdir / 'index.html').read_text()
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
            '  foo [href="http://www.google.com/"];\n'
            '  foo -> bar;\n'
            '}\n')
    content = ('<map id="%3" name="%3">\n'
               '<area shape="poly" id="node1" href="http://www.google.com/" title="foo" alt=""'
               ' coords="77,29,76,22,70,15,62,10,52,7,41,5,30,7,20,10,12,15,7,22,5,29,7,37,12,'
               '43,20,49,30,52,41,53,52,52,62,49,70,43,76,37"/>\n'
               '</map>')
    cmap = ClickableMapDefinition('dummy.map', content, code)
    assert cmap.filename == 'dummy.map'
    assert cmap.id == 'grapviza4ccdd48ce'
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
