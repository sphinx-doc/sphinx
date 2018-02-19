# -*- coding: utf-8 -*-

master_doc = 'index'
html_theme = 'classic'
exclude_patterns = ['_build']

latex_documents = [
    ('index', 'SphinxTests.tex', 'Testing maxlistdepth=10',
     'Georg Brandl', 'howto'),
]

latex_elements = {
    'maxlistdepth': '10',
}
