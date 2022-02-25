from docutils import nodes
from docutils.parsers import Parser


class Parser(Parser):
    supported = ('foo',)

    def parse(self, input, document):
        section = nodes.section(ids=['id1'])
        section += nodes.title('Generated section', 'Generated section')
        document += section

    def get_transforms(self):
        return []
