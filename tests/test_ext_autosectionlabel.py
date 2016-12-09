# -*- coding: utf-8 -*-
"""
    test_ext_autosectionlabel
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.autosectionlabel extension.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import with_app


@with_app('html', testroot='ext-autosectionlabel')
def test_autosectionlabel_html(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'index.html').text()
    html = ('<li><a class="reference internal" href="#introduce-of-sphinx">'
            '<span class=".*?">Introduce of Sphinx</span></a></li>')
    assert re.search(html, content, re.S)

    html = ('<li><a class="reference internal" href="#installation">'
            '<span class="std std-ref">Installation</span></a></li>')
    assert re.search(html, content, re.S)

    html = ('<li><a class="reference internal" href="#for-windows-users">'
            '<span class="std std-ref">For Windows users</span></a></li>')
    assert re.search(html, content, re.S)

    html = ('<li><a class="reference internal" href="#for-unix-users">'
            '<span class="std std-ref">For UNIX users</span></a></li>')
    assert re.search(html, content, re.S)
