# -*- coding: utf-8 -*-
"""
    test_ext_autosectionlabel
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.autosectionlabel extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel')
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

    # for smart_quotes (refs: #4027)
    html = (u'<li><a class="reference internal" '
            u'href="#this-one-s-got-an-apostrophe">'
            u'<span class="std std-ref">This one’s got an apostrophe'
            u'</span></a></li>')
    assert re.search(html, content, re.S)


# Re-use test definition from above, just change the test root directory
@pytest.mark.sphinx('html', testroot='ext-autosectionlabel-prefix-document')
def test_autosectionlabel_prefix_document_html(app, status, warning):
    return test_autosectionlabel_html(app, status, warning)
