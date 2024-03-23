from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx.application import Sphinx
from sphinx.util.typing import ExtensionMetadata


class HelloWorld(Directive):
    def run(self):
        paragraph_node = nodes.paragraph(text='Hello World!')
        return [paragraph_node]


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_directive('helloworld', HelloWorld)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
