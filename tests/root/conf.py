# -*- coding: utf-8 -*-

import sys, os

sys.path.append(os.path.abspath('.'))

extensions = ['ext', 'sphinx.ext.autodoc', 'sphinx.ext.jsmath',
              'sphinx.ext.coverage', 'sphinx.ext.todo',
              'sphinx.ext.autosummary', 'sphinx.ext.doctest']

jsmath_path = 'dummy.js'

templates_path = ['_templates']

master_doc = 'contents'
source_suffix = '.txt'

project = 'Sphinx <Tests>'
copyright = '2008, Georg Brandl & Team'
# If this is changed, remember to update the versionchanges!
version = '0.6'
release = '0.6alpha1'
today_fmt = '%B %d, %Y'
#unused_docs = []
exclude_trees = ['_build']
keep_warnings = True
pygments_style = 'sphinx'

rst_epilog = '.. |subst| replace:: global substitution'

html_theme = 'testtheme'
html_theme_path = ['.']
html_theme_options = {'testopt': 'testoverride'}

html_style = 'default.css'
html_static_path = ['_static']
html_last_updated_fmt = '%b %d, %Y'
html_context = {'hckey': 'hcval', 'hckey_co': 'wrong_hcval_co'}

htmlhelp_basename = 'SphinxTestsdoc'

latex_documents = [
  ('contents', 'SphinxTests.tex', 'Sphinx Tests Documentation',
   'Georg Brandl \\and someone else', 'manual'),
]

latex_additional_files = ['svgimg.svg']

value_from_conf_py = 84

coverage_c_path = ['special/*.h']
coverage_c_regexes = {'cfunction': r'^PyAPI_FUNC\(.*\)\s+([^_][\w_]+)'}

autosummary_generate = ['autosummary']

# modify tags from conf.py
tags.add('confpytag')

from sphinx import addnodes

def userdesc_parse(env, sig, signode):
    x, y = sig.split(':')
    signode += addnodes.desc_name(x, x)
    signode += addnodes.desc_parameterlist()
    signode[-1] += addnodes.desc_parameter(y, y)
    return x

def setup(app):
    app.add_config_value('value_from_conf_py', 42, False)
    app.add_description_unit('userdesc', 'userdescrole', '%s (userdesc)',
                             userdesc_parse)
