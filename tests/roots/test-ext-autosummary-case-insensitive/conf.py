import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autosummary_filename_map = {'casefoo.foo': 'casefoo.foo-module'}
