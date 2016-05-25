# -*- coding: utf-8 -*-

from docutils.parsers import Parser


class DummyMarkdownParser(Parser):
    def parse(self, inputstring, document):
        document.rawsource = inputstring


def setup(app):
    app.add_source_parser('.md', DummyMarkdownParser)
