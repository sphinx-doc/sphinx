import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autodoc_default_options = {'members': True}
templates_path = ['_templates']
