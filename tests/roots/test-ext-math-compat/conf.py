# -*- coding: utf-8 -*-

from docutils.parsers.rst import Directive

from sphinx.ext.mathbase import math, displaymath

master_doc = 'index'
extensions = ['sphinx.ext.mathjax']


def my_math_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    return [math(latex='E = mc^2')], []


class MyMathDirective(Directive):
    def run(self):
        return [displaymath(latex='E = mc^2')]


def setup(app):
    app.add_role('my_math', my_math_role)
    app.add_directive('my-math', MyMathDirective)
