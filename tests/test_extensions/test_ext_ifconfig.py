"""Test sphinx.ext.ifconfig extension."""

import docutils.utils
import pytest

from sphinx import addnodes
from sphinx.testing import restructuredtext


@pytest.mark.sphinx('text', testroot='ext-ifconfig')
def test_ifconfig(app):
    app.build(force_all=True)
    result = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert 'spam' in result
    assert 'ham' not in result


@pytest.mark.sphinx('html', testroot='root')
def test_ifconfig_content_line_number(app):
    app.setup_extension('sphinx.ext.ifconfig')
    text = '.. ifconfig:: confval1\n\n   Some link here: :ref:`abc`\n'
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 3
