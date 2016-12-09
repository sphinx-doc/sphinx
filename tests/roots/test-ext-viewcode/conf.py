# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.abspath('.'))
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
master_doc = 'index'
exclude_patterns = ['_build']


if 'test_linkcode' in tags:
    extensions.remove('sphinx.ext.viewcode')
    extensions.append('sphinx.ext.linkcode')

    def linkcode_resolve(domain, info):
        if domain == 'py':
            fn = info['module'].replace('.', '/')
            return "http://foobar/source/%s.py" % fn
        elif domain == "js":
            return "http://foobar/js/" + info['fullname']
        elif domain in ("c", "cpp"):
            return "http://foobar/%s/%s" % (domain,  "".join(info['names']))
        else:
            raise AssertionError()
