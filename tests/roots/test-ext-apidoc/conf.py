from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / 'src'))

extensions = ["sphinx.ext.apidoc"]

apidoc_modules = [
    {
        'path': 'src', 
        'destination': 'generated',
        'exclude_patterns': ['src/exclude_package.py'],
        'automodule_options': ['members', 'undoc-members'],
        'maxdepth': 3,
        'followlinks': False,
        'separatemodules': True,
        'includeprivate': True,
        'noheadings': False,
        'modulefirst': True,
        'implicit_namespaces': False,
    }
]
