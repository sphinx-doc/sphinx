import os
import sys

source_dir = os.path.abspath('.')
if source_dir not in sys.path:
    sys.path.insert(0, source_dir)
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
exclude_patterns = ['_build']
viewcode_show_lineos = True
