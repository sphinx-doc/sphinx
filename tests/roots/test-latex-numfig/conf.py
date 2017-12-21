# -*- coding: utf-8 -*-

master_doc = 'index'

extensions = ['sphinx.ext.imgmath']  # for math_numfig

latex_documents = [
    ('indexmanual', 'SphinxManual.tex', 'Test numfig manual',
     'Sphinx', 'manual'),
    ('indexhowto', 'SphinxHowTo.tex', 'Test numfig howto',
     'Sphinx', 'howto'),
]
