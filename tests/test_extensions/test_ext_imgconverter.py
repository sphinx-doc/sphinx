"""Test sphinx.ext.imgconverter extension."""

import subprocess

import pytest


@pytest.fixture()
def _if_converter_found(app):
    image_converter = getattr(app.config, 'image_converter', '')
    try:
        if image_converter:
            # print the image_converter version, to check that the command is available
            subprocess.run([image_converter, '-version'], capture_output=True, check=False)
            return
    except OSError:  # No such file or directory
        pass

    pytest.skip('image_converter "%s" is not available' % image_converter)


@pytest.mark.usefixtures('_if_converter_found')
@pytest.mark.sphinx('latex', testroot='ext-imgconverter')
def test_ext_imgconverter(app, status, warning):
    app.build(force_all=True)

    content = (app.outdir / 'python.tex').read_text(encoding='utf8')

    # supported image (not converted)
    assert '\\sphinxincludegraphics{{img}.pdf}' in content

    # non supported image (converted)
    assert '\\sphinxincludegraphics{{svgimg}.png}' in content
    assert not (app.outdir / 'svgimg.svg').exists()
    assert (app.outdir / 'svgimg.png').exists()
