import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd().resolve()))

from docutils import nodes
from docutils.parsers.rst import Directive

from sphinx import addnodes

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.extlinks',
]

jsmath_path = 'dummy.js'

templates_path = ['_templates']

source_suffix = {
    '.txt': 'restructuredtext',
    '.foo': 'foo',
}

project = 'Sphinx <Tests>'
copyright = '1234-6789, copyright text credits'
# If this is changed, remember to update the versionchanges!
version = '0.6'
release = '0.6alpha1'
today_fmt = '%B %d, %Y'
exclude_patterns = ['_build', '**/excluded.*']
keep_warnings = True
pygments_style = 'sphinx'
show_authors = True
numfig = True
linkcheck_timeout = 0.25

html_sidebars = {
    '**': [
        'localtoc.html',
        'relations.html',
        'sourcelink.html',
        'customsb.html',
        'searchbox.html',
    ],
    'index': ['contentssb.html', 'localtoc.html', 'globaltoc.html'],
}
html_last_updated_fmt = '%b %d, %Y'
html_context = {'hckey': 'hcval', 'hckey_co': 'wrong_hcval_co'}

latex_additional_files = ['svgimg.svg']
# some random pdf layout parameters to check they don't break build
latex_elements = {
    'sphinxsetup': """
  verbatimwithframe,
  verbatimwrapslines,
  verbatimforcewraps,
  verbatimmaxoverfull=1,
  verbatimmaxunderfull=5,
  verbatimhintsturnover=true,
  verbatimcontinuesalign=l,
  VerbatimColor={RGB}{242,242,242},
  VerbatimBorderColor={RGB}{32,32,32},
  VerbatimHighlightColor={RGB}{200,200,200},
  pre_box-decoration-break=slice,
  pre_border-top-left-radius=20pt,
  pre_border-top-right-radius=0pt,
  pre_border-bottom-right-radius=20pt,
  pre_border-bottom-left-radius=0pt,
  verbatimsep=1pt,
  pre_padding=5pt,% alias to verbatimsep
  pre_border-top-width=5pt,
  pre_border-right-width=10pt,
  pre_border-bottom-width=15pt,
  pre_border-left-width=20pt,
  pre_border-width=3pt,% overrides all previous four
  verbatimborder=2pt,% alias to pre_border-width
%
  shadowrule=1pt,
  shadowsep=10pt,
  shadowsize=-10pt,
  div.topic_border-width=2pt,
  div.topic_padding=6pt,
  div.topic_box-shadow=5pt,
  div.contents_border-width=3pt,
  div.contents_padding=10pt,
  div.contents_box-shadow=none,
  div.sidebar_border-width=0pt,
  div.sidebar_border-radius=0pt,
%
  noteBorderColor={RGB}{204,204,204},
  hintBorderColor={RGB}{204,204,204},
  importantBorderColor={RGB}{204,204,204},
  tipBorderColor={RGB}{204,204,204},
%
  noteborder=5pt,
  hintborder=5pt,
  importantborder=5pt,
  tipborder=5pt,
%
  warningborder=3pt,
  cautionborder=3pt,
  attentionborder=3pt,
  errorborder=3pt,
%
  dangerborder=3pt,
  div.danger_border-width=10pt,
  div.danger_background-TeXcolor={rgb}{0,1,0},
  div.danger_border-TeXcolor={rgb}{0,0,1},
  div.danger_box-shadow=20pt -20pt,
  div.danger_box-shadow-TeXcolor={rgb}{0.5,0.5,0.5},
%
  warningBorderColor={RGB}{255,119,119},
  cautionBorderColor={RGB}{255,119,119},
  attentionBorderColor={RGB}{255,119,119},
  dangerBorderColor={RGB}{255,119,119},
  errorBorderColor={RGB}{255,119,119},
  warningBgColor={RGB}{255,238,238},
  cautionBgColor={RGB}{255,238,238},
  attentionBgColor={RGB}{255,238,238},
  dangerBgColor={RGB}{255,238,238},
  errorBgColor={RGB}{255,238,238},
%
  TableRowColorHeader={rgb}{0,1,0},
  TableRowColorOdd={rgb}{0.5,0,0},
  TableRowColorEven={rgb}{0.1,0.1,0.1},
""",
}

coverage_c_path = ['special/*.h']
coverage_c_regexes = {'function': r'^PyAPI_FUNC\(.*\)\s+([^_][\w_]+)'}

extlinks = {
    'issue': ('https://bugs.python.org/issue%s', 'issue %s'),
    'pyurl': ('https://python.org/%s', None),
}

# modify tags from conf.py
tags.add('confpytag')  # NoQA: F821 (tags is injected into conf.py)


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
    app.add_object_type(
        'userdesc', 'userdescrole', '%s (userdesc)', userdesc_parse, objname='user desc'
    )
    app.add_js_file('file://moo.js')
    app.add_source_suffix('.foo', 'foo')
    app.add_source_parser(parsermod.Parser)
