import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc']

autodoc_mock_imports = [
    'dummy'
]

nitpicky = True

if sys.version_info < (3, 7):
    exclude_patterns = ['index_py37.rst']
