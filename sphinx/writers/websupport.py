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
    commentable_nodes = ['bullet_list', 'paragraph', 'desc']

    def __init__(self, builder, *args, **kwargs):
        HTMLTranslator.__init__(self, builder, *args, **kwargs)
        self.init_support()

    def init_support(self):
        self.support_document = Document()
        self.in_commentable = False
        self.current_id = 0
        
    def dispatch_visit(self, node):
        if node.__class__.__name__ in self.commentable_nodes:
            self.handle_visit_commentable(node)
        HTMLTranslator.dispatch_visit(self, node)

    def dispatch_departure(self, node):
        HTMLTranslator.dispatch_departure(self, node)
        if node.__class__.__name__ in self.commentable_nodes:
            self.handle_depart_commentable(node)

    def handle_visit_commentable(self, node):
        # If we are already recording a commentable slice we don't do
        # anything. We can't handle nesting.
        if not self.in_commentable:
            self.support_document.add_slice(''.join(self.body))
            node.commented = self.in_commentable = True
            self.body = []
        else:
            node.commented = False

    def handle_depart_commentable(self, node):
        assert(self.in_commentable)
        if node.commented:
            slice_id = '%s-%s' % (self.builder.docname, self.current_id)
            self.current_id += 1

            body = ''.join(self.body)
            self.support_document.add_slice(body, slice_id, commentable=True)

            self.in_commentable = False
            self.body = []

    def depart_document(self, node):
        assert(not self.in_commentable)
        self.support_document.add_slice(''.join(self.body))
                

