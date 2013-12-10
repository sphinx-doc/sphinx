# -*- coding: utf-8 -*-

import sys, os

sys.path.append(os.path.abspath('.'))
sys.path.append(os.path.abspath('..'))

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.jsmath', 'sphinx.ext.todo',
              'sphinx.ext.coverage', 'sphinx.ext.autosummary',
              'sphinx.ext.doctest', 'sphinx.ext.extlinks',
              'sphinx.ext.viewcode', 'sphinx.ext.oldcmarkup', 'ext']

jsmath_path = 'dummy.js'

templates_path = ['_templates']

master_doc = 'contents'
source_suffix = '.txt'

project = 'Sphinx <Tests>'
copyright = '2010, Georg Brandl & Team'
# If this is changed, remember to update the versionchanges!
version = '0.6'
release = '0.6alpha1'
today_fmt = '%B %d, %Y'
# unused_docs = []
exclude_patterns = ['_build', '**/excluded.*']
keep_warnings = True
pygments_style = 'sphinx'
show_authors = True

rst_epilog = '.. |subst| replace:: global substitution'

html_theme = 'testtheme'
html_theme_path = ['.']
html_theme_options = {'testopt': 'testoverride'}
html_sidebars = {'**': 'customsb.html',
                 'contents': ['contentssb.html', 'localtoc.html'] }
html_style = 'default.css'
html_static_path = ['_static', 'templated.css_t']
html_extra_path = ['robots.txt']
html_last_updated_fmt = '%b %d, %Y'
html_context = {'hckey': 'hcval', 'hckey_co': 'wrong_hcval_co'}

htmlhelp_basename = 'SphinxTestsdoc'

latex_documents = [
  ('contents', 'SphinxTests.tex', 'Sphinx Tests Documentation',
   'Georg Brandl \\and someone else', 'manual'),
]

latex_additional_files = ['svgimg.svg']

texinfo_documents = [
  ('contents', 'SphinxTests', 'Sphinx Tests',
   'Georg Brandl \\and someone else', 'Sphinx Testing', 'Miscellaneous'),
]

man_pages = [
    ('contents', 'SphinxTests', 'Sphinx Tests Documentation',
     'Georg Brandl and someone else', 1),
]

value_from_conf_py = 84

coverage_c_path = ['special/*.h']
coverage_c_regexes = {'function': r'^PyAPI_FUNC\(.*\)\s+([^_][\w_]+)'}

autosummary_generate = ['autosummary']

extlinks = {'issue': ('http://bugs.python.org/issue%s', 'issue '),
            'pyurl': ('http://python.org/%s', None)}

# modify tags from conf.py
tags.add('confpytag')

# -- linkcode

if 'test_linkcode' in tags:
    import glob

    extensions.remove('sphinx.ext.viewcode')
    extensions.append('sphinx.ext.linkcode')

    exclude_patterns.extend(glob.glob('*.txt') + glob.glob('*/*.txt'))
    exclude_patterns.remove('contents.txt')
    exclude_patterns.remove('objects.txt')

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

# -- extension API

from docutils import nodes
from sphinx import addnodes
from sphinx.util.compat import Directive

def userdesc_parse(env, sig, signode):
    x, y = sig.split(':')
    signode += addnodes.desc_name(x, x)
    signode += addnodes.desc_parameterlist()
    signode[-1] += addnodes.desc_parameter(y, y)
    return x

def functional_directive(name, arguments, options, content, lineno,
                         content_offset, block_text, state, state_machine):
    return [nodes.strong(text='from function: %s' % options['opt'])]

class ClassDirective(Directive):
    option_spec = {'opt': lambda x: x}
    def run(self):
        return [nodes.strong(text='from class: %s' % self.options['opt'])]

def setup(app):
    app.add_config_value('value_from_conf_py', 42, False)
    app.add_directive('funcdir', functional_directive, opt=lambda x: x)
    app.add_directive('clsdir', ClassDirective)
    app.add_object_type('userdesc', 'userdescrole', '%s (userdesc)',
                        userdesc_parse, objname='user desc')
    app.add_javascript('file://moo.js')
