# -*- coding: utf-8 -*-
"""
    test_ext_graphviz
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.graphviz extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import with_app, SkipTest


@with_app('html', testroot='ext-graphviz')
def test_graphviz_html(app, status, warning):
    app.builder.build_all()
    if "dot command 'dot' cannot be run" in warning.getvalue():
        raise SkipTest('graphviz "dot" is not available')

    content = (app.outdir / 'index.html').text()
    html = ('<div class="figure" .*?>\s*<img .*?/>\s*<p class="caption">'
            '<span class="caption-text">caption of graph</span>.*</p>\s*</div>')
    assert re.search(html, content, re.S)

    html = 'Hello <img .*?/>\n graphviz world'
    assert re.search(html, content, re.S)


@with_app('latex', testroot='ext-graphviz')
def test_graphviz_latex(app, status, warning):
    app.builder.build_all()
    if "dot command 'dot' cannot be run" in warning.getvalue():
        raise SkipTest('graphviz "dot" is not available')

    content = (app.outdir / 'SphinxTests.tex').text()
    macro = ('\\\\begin{figure}\[htbp\]\n\\\\centering\n\\\\capstart\n\n'
             '\\\\includegraphics{graphviz-\w+.pdf}\n'
             '\\\\caption{caption of graph}\\\\end{figure}')
    assert re.search(macro, content, re.S)

    macro = 'Hello \\\\includegraphics{graphviz-\w+.pdf} graphviz world'
    assert re.search(macro, content, re.S)
