# -*- coding: utf-8 -*-

import sys, os

sys.path.append(os.path.abspath('.'))

extensions = ['ext', 'sphinx.ext.autodoc', 'sphinx.ext.jsmath',
              'sphinx.ext.coverage', 'sphinx.ext.todo']

jsmath_path = 'dummy.js'

templates_path = ['_templates']

master_doc = 'contents'
source_suffix = '.txt'

project = 'Sphinx <Tests>'
copyright = '2008, Georg Brandl & Team'
version = '0.6'
release = '0.6alpha1'
today_fmt = '%B %d, %Y'
#unused_docs = []
exclude_trees = ['_build']
keep_warnings = True
pygments_style = 'sphinx'

html_style = 'default.css'
html_static_path = ['_static']
html_last_updated_fmt = '%b %d, %Y'
html_context = {'hckey': 'hcval'}

htmlhelp_basename = 'SphinxTestsdoc'

latex_documents = [
  ('contents', 'SphinxTests.tex', 'Sphinx Tests Documentation',
   'Georg Brandl', 'manual'),
]

value_from_conf_py = 84

coverage_c_path = ['special/*.h']
coverage_c_regexes = {'cfunction': r'^PyAPI_FUNC\(.*\)\s+([^_][\w_]+)'}


def setup(app):
    app.add_config_value('value_from_conf_py', 42, False)
