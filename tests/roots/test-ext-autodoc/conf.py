import os
import sys

sys.path.insert(0, os.path.abspath('.'))

extensions = ['sphinx.ext.autodoc']

# The suffix of source filenames.
source_suffix = '.rst'

autodoc_mock_imports = [
    'dummy'
]

nitpicky = True
