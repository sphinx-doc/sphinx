# -*- coding: utf-8 -*-

master_doc = 'index'
html_theme = 'classic'
templates_path = ['_templates']


def setup(app):
    app.add_stylesheet('persistent.css')
    app.add_stylesheet('default.css', title="Default")
    app.add_stylesheet('alternate1.css', title="Alternate", alternate=True)
    app.add_stylesheet('alternate2.css', alternate=True)
