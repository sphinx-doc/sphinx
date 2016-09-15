# -*- coding: utf-8 -*-
"""
    sphinx.transforms.compact_bullet_list
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx when reading documents.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.transforms import Transform

from sphinx import addnodes


class RefOnlyListChecker(nodes.GenericNodeVisitor):
    """Raise `nodes.NodeFound` if non-simple list item is encountered.

    Here 'simple' means a list item containing only a paragraph with a
    single reference in it.
    """

    def default_visit(self, node):
        raise nodes.NodeFound

    def visit_bullet_list(self, node):
        pass

    def visit_list_item(self, node):
        children = []
        for child in node.children:
            if not isinstance(child, nodes.Invisible):
                children.append(child)
        if len(children) != 1:
            raise nodes.NodeFound
        if not isinstance(children[0], nodes.paragraph):
            raise nodes.NodeFound
        para = children[0]
        if len(para) != 1:
            raise nodes.NodeFound
        if not isinstance(para[0], addnodes.pending_xref):
            raise nodes.NodeFound
        raise nodes.SkipChildren

    def invisible_visit(self, node):
        """Invisible nodes should be ignored."""
        pass


class RefOnlyBulletListTransform(Transform):
    """Change refonly bullet lists to use compact_paragraphs.

    Specifically implemented for 'Indices and Tables' section, which looks
    odd when html_compact_lists is false.
    """
    default_priority = 100

    def apply(self):
        env = self.document.settings.env
        if env.config.html_compact_lists:
            return

        def check_refonly_list(node):
            """Check for list with only references in it."""
            visitor = RefOnlyListChecker(self.document)
            try:
                node.walk(visitor)
            except nodes.NodeFound:
                return False
            else:
                return True

        for node in self.document.traverse(nodes.bullet_list):
            if check_refonly_list(node):
                for item in node.traverse(nodes.list_item):
                    para = item[0]
                    ref = para[0]
                    compact_para = addnodes.compact_paragraph()
                    compact_para += ref
                    item.replace(para, compact_para)
