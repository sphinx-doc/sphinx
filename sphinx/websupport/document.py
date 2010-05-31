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
        self.slices = []

    def add_slice(self, html, id=None, commentable=False):
        slice = HTMLSlice(html, id, commentable)
        self.slices.append(slice)

class HTMLSlice(object):
    def __init__(self, html, id, commentable):
        self.html = html
        self.id = id
        self.commentable = commentable
