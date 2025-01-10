import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autosummary_filename_map = {
    'autosummary_dummy_module': 'module_mangled',
    'autosummary_dummy_module.bar': 'bar',
}
