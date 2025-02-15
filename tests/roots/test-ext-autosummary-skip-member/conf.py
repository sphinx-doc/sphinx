import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autosummary']
autosummary_generate = True
autodoc_default_options = {'members': True}


def skip_member(app, what, name, obj, skip, options) -> bool | None:
    if name == 'skipmeth':
        return True
    elif name == '_privatemeth':
        return False
    return None


def setup(app) -> None:
    app.connect('autodoc-skip-member', skip_member)
