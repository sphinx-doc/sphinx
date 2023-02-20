"""Test object description directives."""

import docutils.utils
import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.io import create_publisher
from sphinx.testing import restructuredtext
from sphinx.util.docutils import sphinx_domains


def _doctree_for_test(builder, docname: str) -> nodes.document:
    builder.env.prepare_settings(docname)
    publisher = create_publisher(builder.app, 'restructuredtext')
    with sphinx_domains(builder.env):
        publisher.set_source(source_path=builder.env.doc2path(docname))
        publisher.publish()
        return publisher.document


@pytest.mark.sphinx('text', testroot='object-description-sections')
def test_object_description_sections(app):
    doctree = _doctree_for_test(app.builder, 'index')
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


def test_object_description_content_line_number(app):
    text = (".. py:function:: foo(bar)\n" +
            "\n" +
            "   Some link here: :ref:`abc`\n")
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 3
