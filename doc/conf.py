# Sphinx documentation build configuration file

import re

import sphinx

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.todo',
              'sphinx.ext.autosummary', 'sphinx.ext.extlinks',
              'sphinx.ext.intersphinx',
              'sphinx.ext.viewcode', 'sphinx.ext.inheritance_diagram']

root_doc = 'contents'
templates_path = ['_templates']
exclude_patterns = ['_build']

project = 'Sphinx'
copyright = '2007-2022, Georg Brandl and the Sphinx team'
version = sphinx.__display_version__
release = version
show_authors = True

html_theme = 'sphinx13'
html_theme_path = ['_themes']
modindex_common_prefix = ['sphinx.']
html_static_path = ['_static']
html_sidebars = {'index': ['indexsidebar.html', 'searchbox.html']}
html_title = 'Sphinx documentation'
html_additional_pages = {'index': 'index.html'}
html_use_opensearch = 'https://www.sphinx-doc.org/en/master'
html_baseurl = 'https://www.sphinx-doc.org/en/master/'
html_favicon = '_static/favicon.svg'

htmlhelp_basename = 'Sphinxdoc'

epub_theme = 'epub'
epub_basename = 'sphinx'
epub_author = 'Georg Brandl'
epub_publisher = 'https://www.sphinx-doc.org/'
epub_uid = 'web-site'
epub_scheme = 'url'
epub_identifier = epub_publisher
epub_pre_files = [('index.xhtml', 'Welcome')]
epub_post_files = [('usage/installation.xhtml', 'Installing Sphinx'),
                   ('develop.xhtml', 'Sphinx development')]
epub_exclude_files = ['_static/opensearch.xml', '_static/doctools.js',
                      '_static/jquery.js', '_static/searchtools.js',
                      '_static/underscore.js', '_static/basic.css',
                      '_static/language_data.js',
                      'search.html', '_static/websupport.js']
epub_fix_images = False
epub_max_image_width = 0
epub_show_urls = 'inline'
epub_use_index = False
epub_guide = (('toc', 'contents.xhtml', 'Table of Contents'),)
epub_description = 'Sphinx documentation generator system manual'

latex_documents = [('contents', 'sphinx.tex', 'Sphinx Documentation',
                    'Georg Brandl', 'manual', 1)]
latex_logo = '_static/sphinx.png'
latex_elements = {
    'fontenc': r'\usepackage[LGR,X2,T1]{fontenc}',
    'passoptionstopackages': r'''
\PassOptionsToPackage{svgnames}{xcolor}
''',
    'preamble': r'''
\DeclareUnicodeCharacter{229E}{\ensuremath{\boxplus}}
\setcounter{tocdepth}{3}%    depth of what main TOC shows (3=subsubsection)
\setcounter{secnumdepth}{1}% depth of section numbering
''',
    # fix missing index entry due to RTD doing only once pdflatex after makeindex
    'printindex': r'''
\IfFileExists{\jobname.ind}
             {\footnotesize\raggedright\printindex}
             {\begin{sphinxtheindex}\end{sphinxtheindex}}
''',
}
latex_show_urls = 'footnote'
latex_use_xindy = True

autodoc_member_order = 'groupwise'
autosummary_generate = False
todo_include_todos = True
extlinks = {'duref': ('https://docutils.sourceforge.io/docs/ref/rst/'
                      'restructuredtext.html#%s', ''),
            'durole': ('https://docutils.sourceforge.io/docs/ref/rst/'
                       'roles.html#%s', ''),
            'dudir': ('https://docutils.sourceforge.io/docs/ref/rst/'
                      'directives.html#%s', '')}

man_pages = [
    ('contents', 'sphinx-all', 'Sphinx documentation generator system manual',
     'Georg Brandl', 1),
    ('man/sphinx-build', 'sphinx-build', 'Sphinx documentation generator tool',
     '', 1),
    ('man/sphinx-quickstart', 'sphinx-quickstart', 'Sphinx documentation '
     'template generator', '', 1),
    ('man/sphinx-apidoc', 'sphinx-apidoc', 'Sphinx API doc generator tool',
     '', 1),
    ('man/sphinx-autogen', 'sphinx-autogen', 'Generate autodoc stub pages',
     '', 1),
]

texinfo_documents = [
    ('contents', 'sphinx', 'Sphinx Documentation', 'Georg Brandl',
     'Sphinx', 'The Sphinx documentation builder.', 'Documentation tools',
     1),
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'requests': ('https://requests.readthedocs.io/en/master', None),
    'readthedocs': ('https://docs.readthedocs.io/en/stable', None),
}

# Sphinx document translation with sphinx gettext feature uses these settings:
locale_dirs = ['locale/']
gettext_compact = False


# -- Extension interface -------------------------------------------------------

from sphinx import addnodes  # noqa

event_sig_re = re.compile(r'([a-zA-Z-]+)\s*\((.*)\)')


def parse_event(env, sig, signode):
    m = event_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return sig
    name, args = m.groups()
    signode += addnodes.desc_name(name, name)
    plist = addnodes.desc_parameterlist()
    for arg in args.split(','):
        arg = arg.strip()
        plist += addnodes.desc_parameter(arg, arg)
    signode += plist
    return name


def setup(app):
    from sphinx.ext.autodoc import cut_lines
    from sphinx.util.docfields import GroupedField
    app.connect('autodoc-process-docstring', cut_lines(4, what=['module']))
    app.add_object_type('confval', 'confval',
                        objname='configuration value',
                        indextemplate='pair: %s; configuration value')
    app.add_object_type('setuptools-confval', 'setuptools-confval',
                        objname='setuptools configuration value',
                        indextemplate='pair: %s; setuptools configuration value')
    fdesc = GroupedField('parameter', label='Parameters',
                         names=['param'], can_collapse=True)
    app.add_object_type('event', 'event', 'pair: %s; event', parse_event,
                        doc_field_types=[fdesc])

    # workaround for RTD
    from sphinx.util import logging
    logger = logging.getLogger(__name__)
    app.info = lambda *args, **kwargs: logger.info(*args, **kwargs)
    app.warn = lambda *args, **kwargs: logger.warning(*args, **kwargs)
    app.debug = lambda *args, **kwargs: logger.debug(*args, **kwargs)
