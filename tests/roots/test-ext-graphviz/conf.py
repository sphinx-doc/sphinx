# -*- coding: utf-8 -*-

extensions = ['sphinx.ext.graphviz']
master_doc = 'index'
exclude_patterns = ['_build']

latex_documents = [
    (master_doc, 'SphinxTests.tex', 'Sphinx Tests Documentation',
     'Georg Brandl', 'manual'),
]
