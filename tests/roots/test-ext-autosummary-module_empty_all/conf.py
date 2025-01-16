import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.autosummary']
autodoc_default_options = {'members': True}
autosummary_ignore_module_all = False
autosummary_imorted_members = False

templates_path = ['templates']
