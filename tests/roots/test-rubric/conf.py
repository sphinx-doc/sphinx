from docutils import nodes
from sphinx.util.docutils import SphinxDirective


class TestRubric(SphinxDirective):
    def run(self):
        return [nodes.section('',
            nodes.rubric('Rubric Title', 'Rubric Title'),
            nodes.Text('Lorem ipsum.'),
            ids=['rubric-permalink-name']
        )]


def setup(app):
    app.add_directive('test_rubric', TestRubric)
