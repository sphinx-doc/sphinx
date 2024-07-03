"""Support for collapsible content in HTML."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives

import sphinx
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec
    from sphinx.writers.html5 import HTML5Translator


class collapsible(nodes.Structural, nodes.Element):
    """Node for collapsible content.

    This is used by the :rst:dir:`collapse` directive.
    """


class summary(nodes.General, nodes.TextElement):
    """Node for the description for collapsible content.

    This is used by the :rst:dir:`collapse` directive.
    """


def visit_collapsible(translator: HTML5Translator, node: nodes.Element) -> None:
    if node.get('open'):
        translator.body.append(translator.starttag(node, 'details', open='open'))
    else:
        translator.body.append(translator.starttag(node, 'details'))


def depart_collapsible(translator: HTML5Translator, node: nodes.Element) -> None:
    translator.body.append('</details>\n')


def visit_summary(translator: HTML5Translator, node: nodes.Element) -> None:
    translator.body.append(translator.starttag(node, 'summary'))


def depart_summary(translator: HTML5Translator, node: nodes.Element) -> None:
    translator.body.append('</summary>\n')


class Collapsible(SphinxDirective):
    """
    Directive to mark collapsible content, with an optional summary line.
    """

    has_content = True
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec: ClassVar[OptionSpec] = {
        'class': directives.class_option,
        'name': directives.unchanged,
        'open': directives.flag,
    }

    def run(self) -> list[nodes.Node]:
        node = collapsible(classes=['collapsible'], open='open' in self.options)
        if 'class' in self.options:
            node['classes'] += self.options['class']
        self.add_name(node)
        node.document = self.state.document
        self.set_source_info(node)

        if self.arguments:
            # parse the argument as reST
            trimmed_summary = self._dedent_string(self.arguments[0].strip())
            textnodes, messages = self.parse_inline(trimmed_summary, lineno=self.lineno)
            node.append(summary(trimmed_summary, '', *textnodes))
            node += messages
        else:
            label = 'Collapsed Content:'
            node.append(summary(label, label))

        return self.parse_content_to_nodes(allow_section_headings=True)

    @staticmethod
    def _dedent_string(s: str) -> str:
        """Remove common leading indentation."""
        lines = s.expandtabs(4).splitlines()

        # Find minimum indentation of any non-blank lines after the first.
        # If your indent is larger than a million spaces, there's a problem…
        margin = 10**6
        for line in lines[1:]:
            content = len(line.lstrip())
            if content:
                indent = len(line) - content
                margin = min(margin, indent)

        if margin == 10**6:
            return s

        return '\n'.join(lines[:1] + [line[margin:] for line in lines[1:]])


#: This constant can be modified by programmers that create their own
#: HTML builders outside the Sphinx core.
HTML_5_BUILDERS = frozenset({'html', 'dirhtml'})


class CollapsibleNodeTransform(SphinxPostTransform):
    default_priority = 55

    def run(self, **kwargs: Any) -> None:
        """Filter collapsible and collapsible_summary nodes based on HTML 5 support."""
        if self.app.builder.name in HTML_5_BUILDERS:
            return

        for summary_node in self.document.findall(summary):
            summary_para = nodes.paragraph('', '', *summary_node)
            summary_node.replace_self(summary_para)

        for collapsible_node in self.document.findall(collapsible):
            container = nodes.container('', *collapsible_node.children)
            collapsible_node.replace_self(container)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_node(collapsible, html=(visit_collapsible, depart_collapsible))
    app.add_node(summary, html=(visit_summary, depart_summary))
    app.add_directive('collapse', Collapsible)
    app.add_post_transform(CollapsibleNodeTransform)

    return {
        'version': sphinx.__display_version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
