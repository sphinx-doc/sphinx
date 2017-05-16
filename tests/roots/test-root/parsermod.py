from docutils.parsers import Parser
from docutils import nodes


class Parser(Parser):
    def parse(self, input, document):
        section = nodes.section(ids=['id1'])
        section += nodes.title('Generated section', 'Generated section')
        document += section

    def get_transforms(self):
        return []
