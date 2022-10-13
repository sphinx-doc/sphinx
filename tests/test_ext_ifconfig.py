"""Test sphinx.ext.ifconfig extension."""

import pytest


@pytest.mark.sphinx('text', testroot='ext-ifconfig')
def test_ifconfig(app, status, warning):
    app.builder.build_all()
    result = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert 'spam' in result
    assert 'ham' not in result
