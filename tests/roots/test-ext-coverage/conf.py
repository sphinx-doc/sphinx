import os
import sys

sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage']

coverage_ignore_pyobjects = [
    r'^coverage_ignored(\..*)?$',
    r'\.Ignored$',
    r'\.Documented\.ignored\d$',
]
