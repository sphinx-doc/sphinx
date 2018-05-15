# -*- coding: utf-8 -*-

from sphinx.ext.mathbase import math

master_doc = 'index'
extensions = ['sphinx.ext.mathjax']


def my_math_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    return [math(latex='E = mc^2')], []


def setup(app):
    app.add_role('my_math', my_math_role)
