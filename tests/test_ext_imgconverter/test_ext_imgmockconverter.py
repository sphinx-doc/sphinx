"""Test image converter with identical basenames"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx('latex', testroot='ext-imgmockconverter')
def test_ext_imgmockconverter(app: SphinxTestApp) -> None:
    app.build(force_all=True)

    content = (app.outdir / 'projectnamenotset.tex').read_text(encoding='utf8')

    # check identical basenames give distinct files
    assert '\\sphinxincludegraphics{{svgimg}.pdf}' in content
    assert '\\sphinxincludegraphics{{svgimg1}.pdf}' in content
    assert not (app.outdir / 'svgimg.svg').exists()
    assert (app.outdir / 'svgimg.pdf').exists()
    assert (app.outdir / 'svgimg1.pdf').exists()
