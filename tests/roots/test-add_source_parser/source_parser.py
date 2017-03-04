# -*- coding: utf-8 -*-

from docutils.parsers import Parser


class TestSourceParser(Parser):
    pass


def setup(app):
    app.add_source_parser('.test', TestSourceParser)
