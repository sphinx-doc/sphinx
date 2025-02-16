"""Test object description directives."""

from __future__ import annotations

from typing import TYPE_CHECKING

import docutils.utils
import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.io import create_publisher
from sphinx.testing import restructuredtext
from sphinx.util.docutils import sphinx_domains

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.testing.util import SphinxTestApp


def _doctree_for_test(
    app: Sphinx, env: BuildEnvironment, docname: str
) -> nodes.document:
    env.prepare_settings(docname)
    publisher = create_publisher(app, 'restructuredtext')
    with sphinx_domains(env):
        publisher.set_source(source_path=str(env.doc2path(docname)))
        publisher.publish()
        return publisher.document


@pytest.mark.sphinx('text', testroot='object-description-sections')
def test_object_description_sections(app: SphinxTestApp) -> None:
    doctree = _doctree_for_test(app, app.env, 'index')
    # <document>
    #     <index>
    #     <desc>
    #         <desc_signature>
    #             <desc_name>
    #                 func
    #             <desc_parameterlist>
    #         <desc_content>
    #             <section>
    #                 <title>
    #                     Overview
    #                 <paragraph>
    #                     Lorem ipsum dolar sit amet

    assert isinstance(doctree[0], addnodes.index)
    assert isinstance(doctree[1], addnodes.desc)
    assert isinstance(doctree[1][0], addnodes.desc_signature)
    assert isinstance(doctree[1][1], addnodes.desc_content)
    assert isinstance(doctree[1][1][0], nodes.section)
    assert isinstance(doctree[1][1][0][0], nodes.title)
    assert doctree[1][1][0][0][0] == 'Overview'
    assert isinstance(doctree[1][1][0][1], nodes.paragraph)
    assert doctree[1][1][0][1][0] == 'Lorem ipsum dolar sit amet'


@pytest.mark.sphinx('html', testroot='_blank')
def test_object_description_content_line_number(app: SphinxTestApp) -> None:
    text = '.. py:function:: foo(bar)\n\n   Some link here: :ref:`abc`\n'
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 3
