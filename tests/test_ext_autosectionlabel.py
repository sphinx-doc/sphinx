# -*- coding: utf-8 -*-
"""
    test_ext_autosectionlabel
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.autosectionlabel extension.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel')
def test_autosectionlabel_html(app, status, warning, skipped_labels=False):
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

    if skipped_labels is None:
        return

    if not skipped_labels:
        html = ('<li><a class="reference internal" href="#linux">'
                '<span class="std std-ref">Linux</span></a></li>')
        assert re.search(html, content, re.S)

        html = ('<li><a class="reference internal" href="#freebsd">'
                '<span class="std std-ref">FreeBSD</span></a></li>')
        assert re.search(html, content, re.S)
    else:
        html = '<li><span class="xref std std-ref">Linux</span></li>'
        assert re.search(html, content, re.S)

        html = '<li><span class="xref std std-ref">FreeBSD</span></li>'
        assert re.search(html, content, re.S)

        assert 'WARNING: undefined label: linux' in warning.getvalue()
        assert 'WARNING: undefined label: freebsd' in warning.getvalue()


# Re-use test definition from above, just change the test root directory
@pytest.mark.sphinx('html', testroot='ext-autosectionlabel-prefix-document')
def test_autosectionlabel_prefix_document_html(app, status, warning):
    return test_autosectionlabel_html(app, status, warning,
                                      skipped_labels=None)


@pytest.mark.sphinx('html', testroot='ext-autosectionlabel',
                    confoverrides={'autosectionlabel_max_depth': 2})
def test_autosectionlabel_max_depth(app, status, warning):
    return test_autosectionlabel_html(app, status, warning,
                                      skipped_labels=True)
