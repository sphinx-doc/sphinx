"""Test object description directives."""

import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.io import create_publisher
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
