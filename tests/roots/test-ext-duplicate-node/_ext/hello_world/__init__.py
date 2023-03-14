from docutils import nodes
from docutils.parsers.rst import Directive
from hello_world import module_a, module_b

from sphinx.application import Sphinx


class HelloWorld(Directive):

    def run(self):
        paragraph_node = nodes.paragraph(text='Hello World!')
        return [paragraph_node]


def setup(app: Sphinx):  # type: ignore[no-untyped-def]
    app.add_directive("helloworld", HelloWorld)
    module_a.register(app)
    module_b.register(app)

    return {
        'version': '0.1',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
