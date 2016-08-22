# -*- coding: utf-8 -*-
"""
    test_ext_inheritance_diagram
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.inheritance_diagram extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
from util import with_app
from test_ext_graphviz import skip_if_graphviz_not_found


@with_app('html', testroot='ext-inheritance_diagram')
@skip_if_graphviz_not_found
def test_inheritance_diagram_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()

    pattern = ('<div class="figure" id="id1">\n'
               '<img src="_images/inheritance-\w+.png" alt="Inheritance diagram of test.Foo" '
               'class="inheritance"/>\n<p class="caption"><span class="caption-text">'
               'Test Foo!</span><a class="headerlink" href="#id1" '
               'title="Permalink to this image">\xb6</a></p>')
    assert re.search(pattern, content, re.M)


@with_app('latex', testroot='ext-inheritance_diagram')
@skip_if_graphviz_not_found
def test_inheritance_diagram_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'Python.tex').text()

    pattern = ('\\\\begin{figure}\\[htbp]\n\\\\centering\n\\\\capstart\n\n'
               '\\\\includegraphics{inheritance-\\w+.pdf}\n'
               '\\\\caption{Test Foo!}\\\\label{index:id1}\\\\end{figure}')
    assert re.search(pattern, content, re.M)
