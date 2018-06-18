# -*- coding: utf-8 -*-

master_doc = 'index'

latex_documents = [
    (master_doc, 'test.tex', 'The basic Sphinx documentation for testing', 'Sphinx', 'report')
]


def setup(app):
    app.add_crossref_type(directivename="setting", rolename="setting")
