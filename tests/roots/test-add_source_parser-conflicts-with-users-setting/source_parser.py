from docutils.parsers import Parser


class TestSourceParser(Parser):
    supported = ('test',)


def setup(app):
    app.add_source_suffix('.test', 'test')
    app.add_source_parser(TestSourceParser)
