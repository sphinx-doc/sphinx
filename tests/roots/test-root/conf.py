import os
import sys

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx import addnodes

sys.path.append(os.path.abspath('.'))

extensions = ['sphinx.ext.autodoc',
              'sphinx.ext.todo',
              'sphinx.ext.coverage',
              'sphinx.ext.extlinks']

jsmath_path = 'dummy.js'

templates_path = ['_templates']

source_suffix = ['.txt', '.add', '.foo']

project = 'Sphinx <Tests>'
copyright = '2010-2016, Georg Brandl & Team'
# If this is changed, remember to update the versionchanges!
version = '0.6'
release = '0.6alpha1'
today_fmt = '%B %d, %Y'
exclude_patterns = ['_build', '**/excluded.*']
keep_warnings = True
pygments_style = 'sphinx'
show_authors = True
numfig = True

html_sidebars = {'**': ['localtoc.html', 'relations.html', 'sourcelink.html',
                        'customsb.html', 'searchbox.html'],
                 'index': ['contentssb.html', 'localtoc.html', 'globaltoc.html']}
html_last_updated_fmt = '%b %d, %Y'
html_context = {'hckey': 'hcval', 'hckey_co': 'wrong_hcval_co'}

latex_additional_files = ['svgimg.svg']

coverage_c_path = ['special/*.h']
coverage_c_regexes = {'function': r'^PyAPI_FUNC\(.*\)\s+([^_][\w_]+)'}

extlinks = {'issue': ('http://bugs.python.org/issue%s', 'issue %s'),
            'pyurl': ('http://python.org/%s', None)}

# modify tags from conf.py
tags.add('confpytag')  # NOQA


# -- extension API
def userdesc_parse(env, sig, signode):
    x, y = sig.split(':')
    signode += addnodes.desc_name(x, x)
    signode += addnodes.desc_parameterlist()
    signode[-1] += addnodes.desc_parameter(y, y)
    return x


class ClassDirective(Directive):
    option_spec = {'opt': lambda x: x}

    def run(self):
        return [nodes.strong(text='from class: %s' % self.options['opt'])]


def setup(app):
    import parsermod

    app.add_directive('clsdir', ClassDirective)
    app.add_object_type('userdesc', 'userdescrole', '%s (userdesc)',
                        userdesc_parse, objname='user desc')
    app.add_js_file('file://moo.js')
    app.add_source_suffix('.foo', 'foo')
    app.add_source_parser(parsermod.Parser)
