# -*- coding: utf-8 -*-
"""
    test_ext_graphviz
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.graphviz extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('html', testroot='ext-graphviz')
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_png_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = (r'<div class="figure" .*?>\s*<img .*?/>\s*<p class="caption">'
            r'<span class="caption-text">caption of graph</span>.*</p>\s*</div>')
    assert re.search(html, content, re.S)

    html = 'Hello <img .*?/>\n graphviz world'
    assert re.search(html, content, re.S)

    html = '<img src=".*?" alt="digraph {\n  bar -&gt; baz\n}" />'
    assert re.search(html, content, re.M)

    html = (r'<div class="figure align-right" .*?>\s*<img .*?/>\s*<p class="caption">'
            r'<span class="caption-text">on right</span>.*</p>\s*</div>')
    assert re.search(html, content, re.S)

    html = (r'<div align=\"center\" class=\"align-center\">'
            r'<img src=\".*\.png\" alt=\"digraph foo {\n'
            r'centered\n'
            r'}\" />\n</div>')
    assert re.search(html, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-graphviz',
                    confoverrides={'graphviz_output_format': 'svg'})
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_svg_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()

    html = (r'<div class=\"figure\" .*?>\n'
            r'<object data=\".*\.svg\".*>\n'
            r'\s+<p class=\"warning\">digraph foo {\n'
            r'bar -&gt; baz\n'
            r'}</p></object>\n'
            r'<p class=\"caption\"><span class=\"caption-text\">'
            r'caption of graph</span>.*</p>\n</div>')
    assert re.search(html, content, re.S)

    html = (r'Hello <object.*>\n'
            r'\s+<p class=\"warning\">graph</p></object>\n'
            r' graphviz world')
    assert re.search(html, content, re.S)

    html = (r'<div class=\"figure align-right\" .*\>\n'
            r'<object data=\".*\.svg\".*>\n'
            r'\s+<p class=\"warning\">digraph bar {\n'
            r'foo -&gt; bar\n'
            r'}</p></object>\n'
            r'<p class=\"caption\"><span class=\"caption-text\">'
            r'on right</span>.*</p>\n'
            r'</div>')
    assert re.search(html, content, re.S)

    html = (r'<div align=\"center\" class=\"align-center\">'
            r'<object data=\".*\.svg\".*>\n'
            r'\s+<p class=\"warning\">digraph foo {\n'
            r'centered\n'
            r'}</p></object>\n'
            r'</div>')
    assert re.search(html, content, re.S)


@pytest.mark.sphinx('latex', testroot='ext-graphviz')
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'SphinxTests.tex').text()
    macro = ('\\\\begin{figure}\\[htbp\\]\n\\\\centering\n\\\\capstart\n\n'
             '\\\\includegraphics{graphviz-\\w+.pdf}\n'
             '\\\\caption{caption of graph}\\\\label{.*}\\\\end{figure}')
    assert re.search(macro, content, re.S)

    macro = 'Hello \\\\includegraphics{graphviz-\\w+.pdf} graphviz world'
    assert re.search(macro, content, re.S)

    macro = ('\\\\begin{wrapfigure}{r}{0pt}\n\\\\centering\n'
             '\\\\includegraphics{graphviz-\\w+.pdf}\n'
             '\\\\caption{on right}\\\\label{.*}\\\\end{wrapfigure}')
    assert re.search(macro, content, re.S)

    macro = (r'\{\\hfill'
             r'\\includegraphics{graphviz-.*}'
             r'\\hspace\*{\\fill}}')
    assert re.search(macro, content, re.S)


@pytest.mark.sphinx('html', testroot='ext-graphviz', confoverrides={'language': 'xx'})
@pytest.mark.usefixtures('if_graphviz_found')
def test_graphviz_i18n(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = '<img src=".*?" alt="digraph {\n  BAR -&gt; BAZ\n}" />'
    assert re.search(html, content, re.M)
