from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives
from docutils.parsers.rst.roles import set_classes

from sphinx import addnodes
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from docutils.nodes import Element, Node

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec


class BaseAdmonition(SphinxDirective):
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {
        'class': directives.class_option,
        'name': directives.unchanged,
        'collapsible': directives.flag,
        'open': directives.flag,
    }
    has_content = True

    node_class: ClassVar[type[Element]] = nodes.admonition
    """Subclasses must set this to the appropriate admonition node class."""

    def run(self) -> list[Node]:
        set_classes(self.options)
        self.assert_has_content()
        if 'collapsible' in self.options:
            self.options['collapsible'] = True
        if 'open' in self.options:
            self.options['open'] = True
        admonition_node = self.node_class('\n'.join(self.content), **self.options)
        self.add_name(admonition_node)
        if self.node_class is nodes.admonition:
            title_text = self.arguments[0]
            textnodes, messages = self.parse_inline(title_text, lineno=self.lineno)
            title = nodes.title(title_text, '', *textnodes)
            self.set_source_info(title)
            admonition_node += title
            admonition_node += messages
            if 'classes' not in self.options:
                admonition_node['classes'] += ['admonition-' + nodes.make_id(title_text)]
        admonition_node.extend(self.parse_content_to_nodes())
        return [admonition_node]


class Admonition(BaseAdmonition):
    required_arguments = 1
    node_class = nodes.admonition


class Attention(BaseAdmonition):
    node_class = nodes.attention


class Caution(BaseAdmonition):
    node_class = nodes.caution


class Danger(BaseAdmonition):
    node_class = nodes.danger


class Error(BaseAdmonition):
    node_class = nodes.error


class Hint(BaseAdmonition):
    node_class = nodes.hint


class Important(BaseAdmonition):
    node_class = nodes.important


class Note(BaseAdmonition):
    node_class = nodes.note


class Tip(BaseAdmonition):
    node_class = nodes.tip


class Warning(BaseAdmonition):
    node_class = nodes.warning


class SeeAlso(BaseAdmonition):
    """
    An admonition mentioning things to look at as reference.
    """

    node_class = addnodes.seealso


def setup(app: Sphinx) -> ExtensionMetadata:
    directives.register_directive('admonition', Admonition)
    directives.register_directive('attention', Attention)
    directives.register_directive('caution', Caution)
    directives.register_directive('danger', Danger)
    directives.register_directive('error', Error)
    directives.register_directive('hint', Hint)
    directives.register_directive('important', Important)
    directives.register_directive('note', Note)
    directives.register_directive('tip', Tip)
    directives.register_directive('warning', Warning)
    directives.register_directive('seealso', SeeAlso)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
