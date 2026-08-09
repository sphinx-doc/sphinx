"""Test the Sphinx component registry."""

from __future__ import annotations

from unittest.mock import Mock

from docutils import nodes

from sphinx.registry import SphinxComponentRegistry


class FormatNode(nodes.Element):
    pass


class BuilderNode(nodes.Element):
    pass


class OverrideNode(nodes.Element):
    pass


def test_create_translator_combines_builder_and_format_handlers() -> None:
    registry = SphinxComponentRegistry()

    def visit_format(translator: Mock, node: nodes.Element) -> None:
        translator.visited.append(('format', node))

    def visit_builder(translator: Mock, node: nodes.Element) -> None:
        translator.visited.append(('builder', node))

    registry.add_translation_handlers(
        FormatNode,
        html=(visit_format, None),
    )
    registry.add_translation_handlers(
        BuilderNode,
        dirhtml=(visit_builder, None),
    )
    registry.add_translation_handlers(
        OverrideNode,
        html=(visit_format, None),
        dirhtml=(visit_builder, None),
    )

    translator = Mock(visited=[])
    translator_class = Mock(return_value=translator)
    builder = Mock(format='html', default_translator_class=translator_class)
    builder.name = 'dirhtml'

    registry.create_translator(builder)

    format_node = FormatNode()
    builder_node = BuilderNode()
    override_node = OverrideNode()
    translator.visit_FormatNode(format_node)
    translator.visit_BuilderNode(builder_node)
    translator.visit_OverrideNode(override_node)
    assert translator.visited == [
        ('format', format_node),
        ('builder', builder_node),
        ('builder', override_node),
    ]
