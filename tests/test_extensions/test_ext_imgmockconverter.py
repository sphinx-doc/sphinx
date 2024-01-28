"""Test image converter with identical basenames"""

import pytest


@pytest.mark.sphinx('latex', testroot='ext-imgmockconverter')
def test_ext_imgmockconverter(app, status, warning):
    app.build(force_all=True)

    content = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # check identical basenames give distinct files
    assert '\\sphinxincludegraphics{{svgimg}.pdf}' in content
    assert '\\sphinxincludegraphics{{svgimg1}.pdf}' in content
    assert not (app.outdir / 'svgimg.svg').exists()
    assert (app.outdir / 'svgimg.pdf').exists()
    assert (app.outdir / 'svgimg1.pdf').exists()
