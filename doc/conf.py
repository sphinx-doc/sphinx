# Sphinx documentation build configuration file

import os
import re
import time

import sphinx

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.todo',
              'sphinx.ext.autosummary', 'sphinx.ext.extlinks',
              'sphinx.ext.intersphinx',
              'sphinx.ext.viewcode', 'sphinx.ext.inheritance_diagram']

templates_path = ['_templates']
exclude_patterns = ['_build']

project = 'Sphinx'
copyright = f'2007-{time.strftime("%Y")}, the Sphinx developers'
version = sphinx.__display_version__
release = version
show_authors = True

html_theme = 'sphinx13'
html_theme_path = ['_themes']
html_css_files = [
    # 'basic.css',  # included through inheritance from the basic theme
    'sphinx13.css',
]
modindex_common_prefix = ['sphinx.']
html_static_path = ['_static']
html_title = 'Sphinx documentation'
html_additional_pages = {'contents': 'contents.html'}
html_use_opensearch = 'https://www.sphinx-doc.org/en/master'
html_baseurl = 'https://www.sphinx-doc.org/en/master/'
html_favicon = '_static/favicon.svg'

htmlhelp_basename = 'Sphinxdoc'

epub_theme = 'epub'
epub_basename = 'sphinx'
epub_author = 'the Sphinx developers'
epub_publisher = 'https://www.sphinx-doc.org/'
epub_uid = 'web-site'
epub_scheme = 'url'
epub_identifier = epub_publisher
epub_pre_files = [('index.xhtml', 'Welcome')]
epub_post_files = [('usage/installation.xhtml', 'Installing Sphinx'),
                   ('develop.xhtml', 'Sphinx development')]
epub_exclude_files = ['_static/opensearch.xml', '_static/doctools.js',
                      '_static/jquery.js', '_static/searchtools.js',
                      '_static/sphinx_highlight.js',
                      '_static/underscore.js', '_static/basic.css',
                      '_static/language_data.js',
                      'search.html', '_static/websupport.js']
epub_fix_images = False
epub_max_image_width = 0
epub_show_urls = 'inline'
epub_use_index = False
epub_description = 'Sphinx documentation generator system manual'

latex_documents = [('index', 'sphinx.tex', 'Sphinx Documentation',
                    'the Sphinx developers', 'manual', 1)]
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
    'sphinxsetup': """%
VerbatimColor=black!5,% tests 5.3.0 extended syntax
VerbatimBorderColor={RGB}{32,32,32},%
pre_border-radius=3pt,%
pre_box-decoration-break=slice,%
""",
}
latex_show_urls = 'footnote'
latex_use_xindy = True
latex_table_style = ['booktabs', 'colorrows']

autodoc_member_order = 'groupwise'
autosummary_generate = False
todo_include_todos = True
extlinks = {'duref': ('https://docutils.sourceforge.io/docs/ref/rst/'
                      'restructuredtext.html#%s', '%s'),
            'durole': ('https://docutils.sourceforge.io/docs/ref/rst/'
                       'roles.html#%s', '%s'),
            'dudir': ('https://docutils.sourceforge.io/docs/ref/rst/'
                      'directives.html#%s', '%s')}

man_pages = [
    ('index', 'sphinx-all', 'Sphinx documentation generator system manual',
     'the Sphinx developers', 1),
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
    ('index', 'sphinx', 'Sphinx Documentation', 'the Sphinx developers',
     'Sphinx', 'The Sphinx documentation builder.', 'Documentation tools',
     1),
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
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


def linkify_issues_in_changelog(app, docname, source):
    """ Linkify issue references like #123 in changelog to GitHub. """

    if docname == 'changes':
        changelog_path = os.path.join(os.path.dirname(__file__), "../CHANGES")
        # this path trickery is needed because this script can
        # be invoked with different working directories:
        # * running make in docs/
        # * running tox -e docs in the repo root dir

        with open(changelog_path, encoding="utf-8") as f:
            changelog = f.read()

        def linkify(match):
            url = 'https://github.com/sphinx-doc/sphinx/issues/' + match[1]
            return '`{} <{}>`_'.format(match[0], url)

        linkified_changelog = re.sub(r'(?:PR)?#([0-9]+)\b', linkify, changelog)

        source[0] = source[0].replace('.. include:: ../CHANGES', linkified_changelog)


def setup(app):
    from sphinx.ext.autodoc import cut_lines
    from sphinx.util.docfields import GroupedField
    app.connect('autodoc-process-docstring', cut_lines(4, what=['module']))
    app.connect('source-read', linkify_issues_in_changelog)
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
