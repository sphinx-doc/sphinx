# -*- coding: utf-8 -*-

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.util.nodes import split_explicit_title


class my_figure(nodes.figure):
    pass


def visit_my_figure(self, node):
    self.visit_figure(node)


def depart_my_figure(self, node):
    self.depart_figure(node)


class MyFigure(Directive):
    required_arguments = 1
    has_content = True

    def run(self):
        figure_node = my_figure()
        figure_node += nodes.image(uri=self.arguments[0])
        figure_node += nodes.caption(text=''.join(self.content))
        return [figure_node]


def setup(app):
    # my-figure
    app.add_enumerable_node(my_figure, 'figure',
                            html=(visit_my_figure, depart_my_figure))
    app.add_directive('my-figure', MyFigure)
