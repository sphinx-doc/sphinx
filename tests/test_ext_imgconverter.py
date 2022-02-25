"""
    test_ext_imgconverter
    ~~~~~~~~~~~~~~~~~~~~~

    Test sphinx.ext.imgconverter extension.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

import pytest


@pytest.mark.sphinx('latex', testroot='ext-imgconverter')
@pytest.mark.xfail(os.name != 'posix', reason="Not working on windows")
def test_ext_imgconverter(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'python.tex').read_text()

    # supported image (not converted)
    assert '\\sphinxincludegraphics{{img}.pdf}' in content

    # non supported image (converted)
    assert '\\sphinxincludegraphics{{svgimg}.png}' in content
    assert not (app.outdir / 'svgimg.svg').exists()
    assert (app.outdir / 'svgimg.png').exists()
