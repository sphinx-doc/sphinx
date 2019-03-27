import os
import sys
sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autosummary']
templates_path = ['_template']
autosummary_generate = True
autosummary_imported_members = True
