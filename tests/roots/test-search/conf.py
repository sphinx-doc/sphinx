# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, os.path.abspath('.'))
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
master_doc = 'index'
exclude_patterns = ['_build']

html_search_language = 'en'
