import os
import sys

sys.path.insert(0, os.path.abspath('.'))


extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autodoc_default_options = {'members': True}
templates_path = ['_templates']
