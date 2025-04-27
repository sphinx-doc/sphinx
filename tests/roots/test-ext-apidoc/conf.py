import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve() / 'src'))

extensions = ['sphinx.ext.apidoc']

apidoc_include_private = True
apidoc_follow_links = False
apidoc_separate_modules = True
apidoc_no_headings = False
apidoc_module_first = True
apidoc_modules = [
    {
        'path': 'src',
        'destination': 'generated',
        'exclude_patterns': ['src/exclude_package.py'],
        'automodule_options': ['members', 'undoc-members'],
        'max_depth': 3,
        'implicit_namespaces': False,
    }
]
