# -*- coding: utf-8 -*-
"""
    sphinx.writers.websupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    docutils writers handling Sphinx' custom nodes.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.writers.html import HTMLTranslator

class WebSupportTranslator(HTMLTranslator):
    """
    Our custom HTML translator.
    """
    commentable_nodes = ['paragraph']

    def __init__(self, builder, *args, **kwargs):
        HTMLTranslator.__init__(self, builder, *args, **kwargs)
        self.comment_class = 'spxcmt'
        self.init_support()

    def init_support(self):
        self.cur_node = None

    def dispatch_visit(self, node):
        if node.__class__.__name__ in self.commentable_nodes:
            self.handle_visit_commentable(node)
        HTMLTranslator.dispatch_visit(self, node)

    def dispatch_departure(self, node):
        HTMLTranslator.dispatch_departure(self, node)
        if node.__class__.__name__ in self.commentable_nodes:
            self.handle_depart_commentable(node)

    def handle_visit_commentable(self, node):
        # If this node is nested inside another commentable node this
        # node will not be commented.
        if self.cur_node is None:
            self.cur_node = self.add_db_node(node)
            # We will place the node in the HTML id attribute. If the node
            # already has an id (for indexing purposes) put an empty
            # span with the existing id directly before this node's HTML.
            if node.attributes['ids']:
                self.body.append('<span id="%s"></span>'
                                 % node.attributes['ids'][0])
            node.attributes['ids'] = ['s%s' % self.cur_node.id]
            node.attributes['classes'].append(self.comment_class)

    def handle_depart_commentable(self, node):
        if self.comment_class in node.attributes['classes']:
            self.cur_node = None

    def add_db_node(self, node):
        storage = self.builder.app.storage
        db_node_id = storage.add_node(document=self.builder.cur_docname,
                                      line=node.line,
                                      source=node.rawsource or node.astext())
        return db_node_id
