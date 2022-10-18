"""Test sphinx.ext.imgconverter extension."""

import subprocess
from contextlib import suppress

import pytest


@pytest.fixture
def if_converter_found(app):
    image_converter = getattr(app.config, 'image_converter', '')
    with suppress(OSError):  # No such file or directory
        if image_converter:
            subprocess.run([image_converter, '-version'], capture_output=True)  # show version
            return

    pytest.skip('image_converter "%s" is not available' % image_converter)


@pytest.mark.usefixtures('if_converter_found')
@pytest.mark.sphinx('latex', testroot='ext-imgconverter')
def test_ext_imgconverter(app, status, warning):
    app.builder.build_all()

    content = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # supported image (not converted)
    assert '\\sphinxincludegraphics{{img}.pdf}' in content

    # non supported image (converted)
    assert '\\sphinxincludegraphics{{svgimg}.png}' in content
    assert not (app.outdir / 'svgimg.svg').exists()
    assert (app.outdir / 'svgimg.png').exists()
