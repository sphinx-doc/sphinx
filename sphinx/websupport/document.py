# -*- coding: utf-8 -*-
"""
    sphinx.websupport.document
    ~~~~~~~~~~~~~~~~~~~~

    Contains a Document class for working with Sphinx documents.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path

from jinja2 import Template
from docutils import nodes
from sphinx import addnodes

class Document(object):
    """A single Document such as 'index'."""
    def __init__(self):
        self.commentable_nodes = []
        self.template = None

    def add_commentable(self, node_id, rst_source=''):
        node = CommentableNode(node_id, rst_source)

    def render_comment(self, id):
        return self.comment_template.render(id=id)

    def render_html(self, comments=False):
        template = Template(self.body)
        return template.render(render_comment=self.render_comment)

class CommentableNode(object):
    def __init__(self, id, rst_source=''):
        self.id = id
        self.rst_source=''
