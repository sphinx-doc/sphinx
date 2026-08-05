"""Test object description directives."""

from __future__ import annotations

from typing import TYPE_CHECKING

import docutils.utils
import pytest
from docutils import nodes

from sphinx import addnodes
from sphinx.testing import restructuredtext
from sphinx.util.docutils import _parse_str_to_doctree

from tests.utils import extract_node

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.environment import BuildEnvironment
    from sphinx.testing.util import SphinxTestApp


def _doctree_for_test(
    app: Sphinx, env: BuildEnvironment, docname: str
) -> nodes.document:
    config = app.config
    registry = app.registry

    filename = env.doc2path(docname)
    content = filename.read_text(encoding='utf-8')

    env.prepare_settings(docname)
    parser = registry.create_source_parser('restructuredtext', config=config, env=env)
    return _parse_str_to_doctree(
        content,
        filename=filename,
        default_settings={'env': env},
        env=env,
        parser=parser,
        transforms=registry.get_transforms(),
    )


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
    assert isinstance(extract_node(doctree, 1, 0), addnodes.desc_signature)
    assert isinstance(extract_node(doctree, 1, 1), addnodes.desc_content)
    assert isinstance(extract_node(doctree, 1, 1, 0), nodes.section)
    assert isinstance(extract_node(doctree, 1, 1, 0, 0), nodes.title)
    assert extract_node(doctree, 1, 1, 0, 0, 0) == 'Overview'
    assert isinstance(extract_node(doctree, 1, 1, 0, 1), nodes.paragraph)
    assert extract_node(doctree, 1, 1, 0, 1, 0) == 'Lorem ipsum dolar sit amet'


@pytest.mark.sphinx('html', testroot='_blank')
def test_object_description_content_line_number(app: SphinxTestApp) -> None:
    text = '.. py:function:: foo(bar)\n\n   Some link here: :ref:`abc`\n'
    doc = restructuredtext.parse(app, text)
    xrefs = list(doc.findall(condition=addnodes.pending_xref))
    assert len(xrefs) == 1
    source, line = docutils.utils.get_source_line(xrefs[0])
    assert 'index.rst' in source
    assert line == 3
