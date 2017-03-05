# -*- coding: utf-8 -*-

from sphinx.writers.html import HTMLTranslator

project = 'test'
master_doc = 'index'


class ConfHTMLTranslator(HTMLTranslator):
    depart_with_node = 0

    def depart_admonition(self, node=None):
        if node is not None:
            self.depart_with_node += 1
        HTMLTranslator.depart_admonition(self, node)


def setup(app):
    app.set_translator('html', ConfHTMLTranslator)
