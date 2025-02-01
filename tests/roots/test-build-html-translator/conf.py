from sphinx.writers.html import HTML5Translator

project = 'test'


class ConfHTMLTranslator(HTML5Translator):
    depart_with_node = 0

    def depart_admonition(self, node=None):
        if node is not None:
            self.depart_with_node += 1
        HTML5Translator.depart_admonition(self, node)


def setup(app):
    app.set_translator('html', ConfHTMLTranslator)
