import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

project = 'test project for doctest + autodoc reporting'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest']
