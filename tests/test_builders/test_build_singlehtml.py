"""Test the SingleFileHTMLBuilder."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('singlehtml', testroot='singlehtml-embed')
def test_singlehtml_embed_assets_disabled_by_default(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # assets are referenced, not embedded
    assert 'href="_static/user.css' in content
    assert 'src="_static/user.js' in content
    assert 'src="_images/img.png"' in content
    assert 'data:image/png;base64,' not in content


@pytest.mark.sphinx(
    'singlehtml',
    testroot='singlehtml-embed',
    confoverrides={'singlehtml_embed_assets': True},
)
def test_singlehtml_embed_assets(app: SphinxTestApp) -> None:
    app.build(force_all=True)
    content = (app.outdir / 'index.html').read_text(encoding='utf8')

    # no references to local stylesheets or scripts remain
    assert 'href="_static/' not in content
    assert 'src="_static/' not in content
    assert 'src="_images/' not in content

    # local stylesheets are inlined, including @import-ed stylesheets
    # and url() references within them
    assert 'p.user-imported' in content
    assert 'background-image: url(data:image/png;base64,' in content

    # local scripts are inlined, with '</script>' escaped so that the
    # script content does not terminate the element early
    assert "const userEmbeddedScript = '<\\/script>';" in content

    # images in the document body are embedded as data URIs
    assert 'src="data:image/png;base64,' in content

    # external assets are left untouched
    assert 'href="https://example.com/external.css"' in content
    assert 'src="https://example.com/external.js"' in content

    # asset files are still written to the output directory
    assert (app.outdir / '_static' / 'user.css').is_file()
    assert (app.outdir / '_images' / 'img.png').is_file()
