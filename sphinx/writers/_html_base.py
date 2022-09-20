"""docutils writers handling Sphinx' custom nodes."""

import re
from typing import TYPE_CHECKING

from docutils import nodes
from docutils.nodes import Element
from docutils.writers.html4css1 import HTMLTranslator as BaseTranslator

from sphinx.locale import _
from sphinx.util import logging
from sphinx.util.docutils import SphinxTranslator

if TYPE_CHECKING:
    from sphinx.builders.html import StandaloneHTMLBuilder


logger = logging.getLogger(__name__)

# A good overview of the purpose behind these classes can be found here:
# http://www.arnebrodowski.de/blog/write-your-own-restructuredtext-writer.html


def multiply_length(length: str, scale: int) -> str:
    """Multiply *length* (width or height) by *scale*."""
    matched = re.match(r'^(\d*\.?\d*)\s*(\S*)$', length)
    if not matched:
        return length
    elif scale == 100:
        return length
    else:
        amount, unit = matched.groups()
        result = float(amount) * scale / 100
        return "%s%s" % (int(result), unit)


class HTMLTranslatorBase(SphinxTranslator, BaseTranslator):
    """
    Our custom HTML translator base.

    This base class is specialised for HTML and HTML5.
    """

    builder: "StandaloneHTMLBuilder"

    def __init__(self, document: nodes.document, builder: "StandaloneHTMLBuilder") -> None:
        super().__init__(document, builder)

        self.highlighter = self.builder.highlighter
        self.docnames = [self.builder.current_docname]  # for singlehtml builder
        self.manpages_url = self.config.manpages_url
        self.protect_literal_text = 0
        self.secnumber_suffix = self.config.html_secnumber_suffix
        self.param_separator = ''
        self.optional_param_level = 0
        self._table_row_indices = [0]
        self._fieldlist_row_indices = [0]
        self.required_params_left = 0

    def visit_start_of_file(self, node: Element) -> None:
        # only occurs in the single-file builder
        self.docnames.append(node['docname'])
        self.body.append('<span id="document-%s"></span>' % node['docname'])

    def depart_start_of_file(self, node: Element) -> None:
        self.docnames.pop()

    #############################################################
    # Domain-specific object descriptions
    #############################################################

    # Top-level nodes for descriptions
    ##################################

    def visit_desc(self, node: Element) -> None:
        self.body.append(self.starttag(node, 'dl'))

    def depart_desc(self, node: Element) -> None:
        self.body.append('</dl>\n\n')

    def visit_desc_signature(self, node: Element) -> None:
        # the id is set automatically
        self.body.append(self.starttag(node, 'dt'))
        self.protect_literal_text += 1

    def depart_desc_signature(self, node: Element) -> None:
        self.protect_literal_text -= 1
        if not node.get('is_multiline'):
            self.add_permalink_ref(node, _('Permalink to this definition'))
        self.body.append('</dt>\n')

    def add_permalink_ref(self, node: Element, title: str) -> None:
        if node['ids'] and self.config.html_permalinks and self.builder.add_permalinks:
            format = '<a class="headerlink" href="#%s" title="%s">%s</a>'
            self.body.append(format % (node['ids'][0], title,
                                       self.config.html_permalinks_icon))
