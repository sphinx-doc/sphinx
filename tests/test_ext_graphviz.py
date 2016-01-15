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
def test_graphviz(app, status, warning):
    app.builder.build_all()
    if "dot command 'dot' cannot be run" in warning.getvalue():
        raise SkipTest('graphviz "dot" is not available')

    content = (app.outdir / 'index.html').text()
    html = ('<p class="graphviz">\s*<img .*?/>\s*</p>\s*'
            '<p class="caption"><span class="caption-text">caption of graph</span>')
    assert re.search(html, content, re.S)
