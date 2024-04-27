"""Support for collapsible content in HTML."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from docutils import nodes
from docutils.parsers.rst import directives

import sphinx
from sphinx.transforms.post_transforms import SphinxPostTransform
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from docutils.parsers.rst.states import RSTState
    from docutils.statemachine import StringList

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata, OptionSpec
    from sphinx.writers.html5 import HTML5Translator


class collapsible(nodes.General, nodes.Element):
    """Node for collapsible content.

    This is used by the :rst:dir:`collapse` directive.
    """


class summary(nodes.General, nodes.TextElement):
    """Node for the description for collapsible content.

    This is used by the :rst:dir:`collapse` directive.
    """


def visit_collapsible(translator: HTML5Translator, node: nodes.Element) -> None:
    if node.get('collapsible_open'):
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
        node = collapsible(
            classes=self.options.get('classes', []),
            collapsible_open='open' in self.options,
        )
        self.add_name(node)
        node.document = self.state.document
        self.set_source_info(node)

        if len(self.arguments) > 0:
            # parse the argument as reST
            trimmed_summary = self._prepare_argument_string(self.arguments[0].strip())
            textnodes, messages = self.state.inline_text(trimmed_summary, self.lineno)
            node.append(summary(trimmed_summary, '', *textnodes))
            node += messages
        else:
            label = 'Collapsed Content:'
            node.append(summary(label, label))

        return self._parse_content(self.state, node, self.content, self.content_offset)

    @staticmethod
    def _prepare_argument_string(s: str) -> str:
        """Prepare a directive argument string.

        Remove common leading indentation, where the indentation of the first
        line is ignored.

        Return a list of lines usable for inserting into a docutils StringList.
        """
        lines = s.expandtabs().splitlines()

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

    @staticmethod
    def _parse_content(
        state: RSTState,
        node: nodes.Element,
        content: StringList,
        offset: int,
    ) -> list[nodes.Node]:
        # Same as util.nested_parse_with_titles but try to handle nested
        # sections which should be raised higher up the doctree.
        memo = state.memo
        surrounding_title_styles = memo.title_styles
        surrounding_section_level = memo.section_level
        memo.title_styles = []
        memo.section_level = 0
        try:
            state.nested_parse(content, offset, node, match_titles=True)
            title_styles = memo.title_styles
            if (
                not surrounding_title_styles
                or not title_styles
                or title_styles[0] not in surrounding_title_styles
                or not state.parent
            ):
                # No nested sections so no special handling needed.
                return [node]
            # Calculate the depths of the current and nested sections.
            current_depth = 0
            parent = state.parent
            while parent:
                current_depth += 1
                parent = parent.parent
            current_depth -= 2
            title_style = title_styles[0]
            nested_depth = len(surrounding_title_styles)
            if title_style in surrounding_title_styles:
                nested_depth = surrounding_title_styles.index(title_style)
            # Use these depths to determine where the nested sections should
            # be placed in the doctree.
            n_sects_to_raise = current_depth - nested_depth + 1
            parent = state.parent
            for _i in range(n_sects_to_raise):
                if parent.parent:
                    parent = parent.parent
            parent.append(node)
            return []
        finally:
            memo.title_styles = surrounding_title_styles
            memo.section_level = surrounding_section_level


# This constant can be modified by programmers that create their own
# HTML builders outside the Sphinx core.
HTML_5_BUILDERS = frozenset({'html', 'dirhtml'})


class CollapsibleNodeTransform(SphinxPostTransform):
    default_priority = 55

    def run(self, **kwargs: Any) -> None:
        self._process_collapsible_nodes(self.document, self.app.builder.name)

    @staticmethod
    def _process_collapsible_nodes(document: nodes.Node, builder_name: str) -> None:
        """Filter collapsible and collapsible_summary nodes based on HTML 5 support."""
        if builder_name in HTML_5_BUILDERS:
            return

        for summary_node in document.findall(summary):
            summary_para = nodes.paragraph('', '', *summary_node)
            summary_node.replace_self(summary_para)

        for collapsible_node in document.findall(collapsible):
            # A comment on the comment() nodes being inserted: replacing by [] would
            # result in a "Losing ids" exception if there is a target node before
            # the only node, so we make sure docutils can transfer the id to
            # something, even if it's just a comment and will lose the id anyway…
            collapsible_children = collapsible_node.children or nodes.comment()
            collapsible_node.replace_self(collapsible_children)


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
