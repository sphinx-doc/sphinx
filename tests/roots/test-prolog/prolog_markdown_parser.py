from docutils.parsers import Parser


class DummyMarkdownParser(Parser):
    supported = ('markdown',)

    def parse(self, inputstring, document) -> None:
        document.rawsource = inputstring


def setup(app) -> None:
    app.add_source_suffix('.md', 'markdown')
    app.add_source_parser(DummyMarkdownParser)
