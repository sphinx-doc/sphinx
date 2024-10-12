import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
exclude_patterns = ['_build']


if 'test_linkcode' in tags:
    extensions.remove('sphinx.ext.viewcode')
    extensions.append('sphinx.ext.linkcode')

    def linkcode_resolve(domain, info):
        if domain == 'py':
            fn = info['module'].replace('.', '/')
            return "https://foobar/source/%s.py" % fn
        elif domain == "js":
            return "https://foobar/js/" + info['fullname']
        elif domain in ("c", "cpp"):
            return f"https://foobar/{domain}/{''.join(info['names'])}"
        else:
            raise AssertionError()
