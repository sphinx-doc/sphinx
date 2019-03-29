from docutils import nodes
from docutils.parsers.rst import Directive

extensions = ['sphinx.ext.mathjax']


def my_math_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    text = 'E = mc^2'
    return [nodes.math(text, text)], []


class MyMathDirective(Directive):
    def run(self):
        text = 'E = mc^2'
        return [nodes.math_block(text, text)]


def setup(app):
    app.add_role('my_math', my_math_role)
    app.add_directive('my-math', MyMathDirective)
