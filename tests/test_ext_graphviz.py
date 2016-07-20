# -*- coding: utf-8 -*-
"""
    test_ext_graphviz
    ~~~~~~~~~~~~~~~~~

    Test sphinx.ext.graphviz extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import subprocess
from functools import wraps

from util import with_app, SkipTest


def skip_if_graphviz_not_found(fn):
    @wraps(fn)
    def decorator(app, *args, **kwargs):
        found = False
        graphviz_dot = getattr(app.config, 'graphviz_dot', '')
        try:
            if graphviz_dot:
                dot = subprocess.Popen([graphviz_dot, '-V'],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)  # show version
                dot.wait()
                found = True
        except OSError:  # No such file or directory
            pass

        if not found:
            raise SkipTest('graphviz "dot" is not available')

        return fn(app, *args, **kwargs)

    return decorator


@with_app('html', testroot='ext-graphviz')
@skip_if_graphviz_not_found
def test_graphviz_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = ('<div class="figure" .*?>\s*<img .*?/>\s*<p class="caption">'
            '<span class="caption-text">caption of graph</span>.*</p>\s*</div>')
    assert re.search(html, content, re.S)

    html = 'Hello <img .*?/>\n graphviz world'
    assert re.search(html, content, re.S)

    html = '<img src=".*?" alt="digraph {\n  bar -&gt; baz\n}" />'
    assert re.search(html, content, re.M)

    html = ('<div class="figure align-right" .*?>\s*<img .*?/>\s*<p class="caption">'
            '<span class="caption-text">on right</span>.*</p>\s*</div>')
    assert re.search(html, content, re.S)


@with_app('latex', testroot='ext-graphviz')
@skip_if_graphviz_not_found
def test_graphviz_latex(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'SphinxTests.tex').text()
    macro = ('\\\\begin{figure}\[htbp\]\n\\\\centering\n\\\\capstart\n\n'
             '\\\\includegraphics{graphviz-\w+.pdf}\n'
             '\\\\caption{caption of graph}\\\\label{.*}\\\\end{figure}')
    assert re.search(macro, content, re.S)

    macro = 'Hello \\\\includegraphics{graphviz-\w+.pdf} graphviz world'
    assert re.search(macro, content, re.S)

    macro = ('\\\\begin{wrapfigure}{r}{0pt}\n\\\\centering\n'
             '\\\\includegraphics{graphviz-\w+.pdf}\n'
             '\\\\caption{on right}\\\\label{.*}\\\\end{wrapfigure}')
    assert re.search(macro, content, re.S)


@with_app('html', testroot='ext-graphviz', confoverrides={'language': 'xx'})
@skip_if_graphviz_not_found
def test_graphviz_i18n(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = '<img src=".*?" alt="digraph {\n  BAR -&gt; BAZ\n}" />'
    assert re.search(html, content, re.M)
