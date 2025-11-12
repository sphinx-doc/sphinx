import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc']

autodoc_mock_imports = [
    'dummy',
]

autodoc_type_aliases = {
    'buffer_like': 'buffer_like',
    'pathlike': 'pathlike',
    'Handler': 'Handler',
}

nitpicky = True
