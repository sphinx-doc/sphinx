import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True


def _skip_member(app, obj_type: str, name: str, obj, skip, options):
    """
    Return True if need to skip. None otherwise.
    """
    if name.startswith('_'):
        return True
    print(f'Checking {name}...')
    return True if name == 'package.skipme' else None


def setup(app):
    """
    Register application handlers:
    """
    app.connect("autodoc-skip-member", _skip_member)
