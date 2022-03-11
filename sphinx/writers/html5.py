"""
    sphinx.writers.html5
    ~~~~~~~~~~~~~~~~~~~~

    Experimental docutils writers for HTML5 handling Sphinx's custom nodes.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Set

from docutils import nodes
from docutils.nodes import Element
from docutils.writers.html5_polyglot import HTMLTranslator as BaseTranslator

import sphinx.writers.html
from sphinx.locale import admonitionlabels
from sphinx.util import logging

logger = logging.getLogger(__name__)

# A good overview of the purpose behind these classes can be found here:
# http://www.arnebrodowski.de/blog/write-your-own-restructuredtext-writer.html


class HTML5Translator(sphinx.writers.html.HTMLTranslatorCommonMixin,
                      BaseTranslator):
    """
    Our custom HTML translator.
    """

    # Override docutils.writers.html5_polyglot:HTMLTranslator
    # otherwise, nodes like <inline classes="s">...</inline> will be
    # converted to <s>...</s> by `visit_inline`.
    supported_inline_tags: Set[str] = set()

    # Nodes for high-level structure in signatures
    ##############################################

    def visit_desc_name(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'span', ''))

    def depart_desc_name(self, node: Element) -> None:
        self.body.append('</span>')

    def visit_desc_addname(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'span', ''))

    def depart_desc_addname(self, node: Element) -> None:
        self.body.append('</span>')

    # overwritten
    def visit_admonition(self, node: Element, name: str = '') -> None:
        self.body.append(self.starttag(
            node, 'div', CLASS=('admonition ' + name)))
        if name:
            node.insert(0, nodes.title(name, admonitionlabels[name]))

    # overwritten to add even/odd classes

    def visit_table(self, node: Element) -> None:
        self._table_row_indices.append(0)

        atts = {}
        classes = [cls.strip(' \t\n') for cls in self.settings.table_style.split(',')]
        classes.insert(0, "docutils")  # compat

        # set align-default if align not specified to give a default style
        classes.append('align-%s' % node.get('align', 'default'))

        if 'width' in node:
            atts['style'] = 'width: %s' % node['width']
        tag = self.starttag(node, 'table', CLASS=' '.join(classes), **atts)
        self.body.append(tag)

    def visit_field(self, node: Element) -> None:
        self._fieldlist_row_indices[-1] += 1
        if self._fieldlist_row_indices[-1] % 2 == 0:
            node['classes'].append('field-even')
        else:
            node['classes'].append('field-odd')
