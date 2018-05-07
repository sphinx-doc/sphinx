# -*- coding: utf-8 -*-

master_doc = 'index'
html_theme = 'classic'
templates_path = ['_templates']


def setup(app):
    app.add_css_file('persistent.css')
    app.add_css_file('default.css', title="Default")
    app.add_css_file('alternate1.css', title="Alternate", rel="alternate stylesheet")
    app.add_css_file('alternate2.css', rel="alternate stylesheet")
