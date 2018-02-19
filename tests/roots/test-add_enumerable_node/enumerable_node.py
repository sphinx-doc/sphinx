# -*- coding: utf-8 -*-

from docutils import nodes
from docutils.parsers.rst import Directive


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


class numbered_text(nodes.Element):
    pass


def visit_numbered_text(self, node):
    self.body.append(self.starttag(node, 'div'))
    self.add_fignumber(node)
    self.body.append(node['title'])
    self.body.append('</div>')
    raise nodes.SkipNode


def get_title(node):
    return node['title']


class NumberedText(Directive):
    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        return [numbered_text(title=self.arguments[0])]


def setup(app):
    # my-figure
    app.add_enumerable_node(my_figure, 'figure',
                            html=(visit_my_figure, depart_my_figure))
    app.add_directive('my-figure', MyFigure)

    # numbered_label
    app.add_enumerable_node(numbered_text, 'original', get_title,
                            html=(visit_numbered_text, None))
    app.add_directive('numbered-text', NumberedText)
    app.config.numfig_format.setdefault('original', 'No.%s')
