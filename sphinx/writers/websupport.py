# -*- coding: utf-8 -*-
"""
    sphinx.writers.websupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    docutils writers handling Sphinx' custom nodes.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.writers.html import HTMLTranslator
from sphinx.websupport.document import Document

class WebSupportTranslator(HTMLTranslator):
    """
    Our custom HTML translator.
    """
    def __init__(self, builder, *args, **kwargs):
        HTMLTranslator.__init__(self, builder, *args, **kwargs)
        self.support_document = Document()
        self.current_id = 0

    def depart_paragraph(self, node):
        HTMLTranslator.depart_paragraph(self, node)
        self.support_document.add_commentable(self.current_id)
        self.body.append("{{ render_comment('%s-p%s') }}" % 
                         (self.builder.docname, self.current_id))
        self.current_id += 1
