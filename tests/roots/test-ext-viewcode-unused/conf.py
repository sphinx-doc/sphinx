import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']


def find_source(app, modname):
    if modname != 'viewcode_unused._types':
        return None

    source = app.srcdir / 'viewcode_unused/_types.py'
    # Model successful source analysis that did not locate the documented object.
    return source.read_text(encoding='utf8'), {}


def setup(app):
    app.connect('viewcode-find-source', find_source)
    return {'parallel_read_safe': True}
