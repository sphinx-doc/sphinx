import re
from pathlib import Path

import docutils
import pytest


@pytest.mark.sphinx('html', testroot='images')
def test_html_remote_images(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<img alt="https://www.python.org/static/img/python-logo.png" '
            'src="https://www.python.org/static/img/python-logo.png" />' in result)
    assert not (app.outdir / 'python-logo.png').exists()


@pytest.mark.sphinx('html', testroot='image-escape')
def test_html_encoded_image(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<img alt="_images/img_%231.png" src="_images/img_%231.png" />' in result)
    assert (app.outdir / '_images/img_#1.png').exists()


@pytest.mark.sphinx('html', testroot='remote-logo')
def test_html_remote_logo(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<img class="logo" src="https://www.python.org/static/img/python-logo.png" alt="Logo"/>' in result)
    assert ('<link rel="icon" href="https://www.python.org/static/favicon.ico"/>' in result)
    assert not (app.outdir / 'python-logo.png').exists()


@pytest.mark.sphinx('html', testroot='local-logo')
def test_html_local_logo(app, status, warning):
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert ('<img class="logo" src="_static/img.png" alt="Logo"/>' in result)
    assert (app.outdir / '_static/img.png').exists()


@pytest.mark.sphinx(testroot='html_scaled_image_link')
def test_html_scaled_image_link(app):
    app.build()
    context = (app.outdir / 'index.html').read_text(encoding='utf8')

    # no scaled parameters
    assert re.search('\n<img alt="_images/img.png" src="_images/img.png" />', context)

    # scaled_image_link
    # Docutils 0.21 adds a newline before the closing </a> tag
    closing_space = "\n" if docutils.__version_info__[:2] >= (0, 21) else ""
    assert re.search('\n<a class="reference internal image-reference" href="_images/img.png">'
                     '<img alt="_images/img.png" src="_images/img.png" style="[^"]+" />'
                     f'{closing_space}</a>',
                     context)

    # no-scaled-link class disables the feature
    assert re.search('\n<img alt="_images/img.png" class="no-scaled-link"'
                     ' src="_images/img.png" style="[^"]+" />',
                     context)


@pytest.mark.sphinx('html', testroot='images')
def test_copy_images(app, status, warning):
    app.build()

    images_dir = Path(app.outdir) / '_images'
    images = {image.name for image in images_dir.rglob('*')}
    assert images == {
        'img.png',
        'rimg.png',
        'rimg1.png',
        'svgimg.svg',
        'testimäge.png',
    }
