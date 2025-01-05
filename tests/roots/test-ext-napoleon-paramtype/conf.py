import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
]

# Python inventory is manually created in the test
# in order to avoid creating a real HTTP connection
intersphinx_mapping = {}
intersphinx_cache_limit = 0
intersphinx_disabled_reftypes = []
