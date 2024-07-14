import os
import sys

sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autosummary_ignore_module_all = False
