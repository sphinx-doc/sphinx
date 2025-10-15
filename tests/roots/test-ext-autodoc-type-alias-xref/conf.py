import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc']
nitpicky = True
autodoc_type_aliases = {
    'pathlike': 'pathlike',
    'Handler': 'Handler',
}
