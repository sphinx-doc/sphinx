import sys
from pathlib import Path

from sphinx.ext.linkcode import add_linkcode_domain

sys.path.insert(0, str(Path.cwd().resolve()))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
exclude_patterns = ['_build']


if 'test_linkcode' in tags:  # NoQA: F821 (tags is injected into conf.py)
    extensions.remove('sphinx.ext.viewcode')
    extensions.append('sphinx.ext.linkcode')

    def linkcode_resolve(domain, info):
        if domain == 'py':
            fn = info['module'].replace('.', '/')
            return 'https://foobar/source/%s.py' % fn
        elif domain == 'js':
            return 'https://foobar/js/' + info['fullname']
        elif domain in {'c', 'cpp'}:
            return f'https://foobar/{domain}/{"".join(info["names"])}'
        elif domain == 'rst':
            return 'http://foobar/rst/{fullname}'.format(**info)
        else:
            raise AssertionError

    def setup(app):
        add_linkcode_domain('rst', ['fullname'])
