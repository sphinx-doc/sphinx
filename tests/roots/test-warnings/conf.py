# -*- coding: utf-8 -*-

import os
import sys
sys.path.append(os.path.abspath('.'))

master_doc = 'index'
extensions = ['sphinx.ext.autodoc']

latex_documents = [
    (master_doc, 'test.tex', 'test-warnings', 'Sphinx', 'report')
]
