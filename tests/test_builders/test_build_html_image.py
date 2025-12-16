from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

import docutils
import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx('html', testroot='images')
def test_html_remote_images(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<img alt="http://localhost:7777/sphinx.png" '
        'src="http://localhost:7777/sphinx.png" />'
    ) in result
    assert not (app.outdir / 'sphinx.png').exists()


@pytest.mark.sphinx('html', testroot='image-escape')
def test_html_encoded_image(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<img alt="_images/img_%231.png" src="_images/img_%231.png" />' in result
    assert (app.outdir / '_images/img_#1.png').exists()


@pytest.mark.sphinx('html', testroot='remote-logo')
def test_html_remote_logo(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<img class="logo" src="https://www.python.org/static/img/python-logo.png" alt="Logo of Project name not set"/>'
    ) in result
    assert (
        '<link rel="icon" href="https://www.python.org/static/favicon.ico"/>'
    ) in result
    assert not (app.outdir / 'python-logo.png').exists()


@pytest.mark.sphinx('html', testroot='local-logo')
def test_html_local_logo(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert (
        '<img class="logo" src="_static/img.png" alt="Logo of Project name not set"/>'
    ) in result
    assert (app.outdir / '_static/img.png').exists()


@pytest.mark.sphinx('html', testroot='html_scaled_image_link')
def test_html_scaled_image_link(app: SphinxTestApp) -> None:
    app.build()
    context = (app.outdir / 'index.html').read_text(encoding='utf8')

    # no scaled parameters
    assert re.search('\n<img alt="_images/img.png" src="_images/img.png" />', context)

    # scaled_image_link
    if docutils.__version_info__[:2] >= (0, 22):
        assert re.search(
            '\n<a class="reference internal image-reference" href="_images/img.png">'
            '<img alt="_images/img.png" height="[^"]+" src="_images/img.png" width="[^"]+" />'
            '\n</a>',
            context,
        )
    else:
        assert re.search(
            '\n<a class="reference internal image-reference" href="_images/img.png">'
            '<img alt="_images/img.png" src="_images/img.png" style="[^"]+" />'
            '\n</a>',
            context,
        )

    # no-scaled-link class disables the feature
    if docutils.__version_info__[:2] >= (0, 22):
        assert re.search(
            '\n<img alt="_images/img.png" class="no-scaled-link"'
            ' height="[^"]+" src="_images/img.png" width="[^"]+" />',
            context,
        )
    else:
        assert re.search(
            '\n<img alt="_images/img.png" class="no-scaled-link"'
            ' src="_images/img.png" style="[^"]+" />',
            context,
        )


@pytest.mark.usefixtures('_http_teapot')
@pytest.mark.sphinx('html', testroot='images')
def test_copy_images(app: SphinxTestApp) -> None:
    app.build()

    images_dir = Path(app.outdir) / '_images'
    images = {image.name for image in images_dir.rglob('*')}
    assert images == {
        # 'ba30773957c3fe046897111afd65a80b81cad089.png',  # html: image from data:image/png URI in source
        'img.png',
        'rimg.png',
        'rimg1.png',
        'svgimg.svg',
        'testimäge.png',
    }
