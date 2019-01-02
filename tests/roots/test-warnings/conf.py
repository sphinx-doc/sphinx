import os
import sys
sys.path.append(os.path.abspath('.'))

extensions = ['sphinx.ext.autodoc']

latex_documents = [
    ('index', 'test.tex', 'test-warnings', 'Sphinx', 'report')
]
