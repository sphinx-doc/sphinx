import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.coverage']

coverage_modules = [
    'grog',
]
coverage_ignore_pyobjects = [
    r'^grog\.coverage_ignored(\..*)?$',
    r'\.Ignored$',
    r'\.Documented\.ignored\d$',
]
