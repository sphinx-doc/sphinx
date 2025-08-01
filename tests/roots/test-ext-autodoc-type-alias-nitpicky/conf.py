import sys
import os
sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autodoc']
nitpicky = True
autodoc_type_aliases = {'pathlike': 'pathlike'}