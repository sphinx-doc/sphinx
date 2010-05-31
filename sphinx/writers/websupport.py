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
        self.init_support()

    def init_support(self):
        self.support_document = Document()
        self.current_id = 0
        
    def handle_visit_commentable(self, node):
        self.support_document.add_slice(''.join(self.body))
        self.body = []

    def handle_depart_commentable(self, node):
        slice_id = '%s-%s' % (self.builder.docname, self.current_id)
        self.support_document.add_slice(''.join(self.body),
                                        slice_id, commentable=True)
        self.body = []
        self.current_id += 1

    def visit_paragraph(self, node):
        HTMLTranslator.visit_paragraph(self, node)
        self.handle_visit_commentable(node)

    def depart_paragraph(self, node):
        HTMLTranslator.depart_paragraph(self, node)
        self.handle_depart_commentable(node)
