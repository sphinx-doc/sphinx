# Sphinx documentation build configuration file
from __future__ import annotations

import os
import re
import time

import sphinx

os.environ['SPHINX_AUTODOC_RELOAD_MODULES'] = '1'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.doctest',
    'sphinx.ext.todo',
    'sphinx.ext.autosummary',
    'sphinx.ext.extlinks',
    'sphinx.ext.intersphinx',
    'sphinx.ext.viewcode',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.coverage',
    'sphinx.ext.graphviz',
    'sphinx.ext.collapse',
]
coverage_statistics_to_report = coverage_statistics_to_stdout = True
templates_path = ['_templates']
exclude_patterns = ['_build']

project = 'Sphinx'
copyright = f'2007-{time.strftime("%Y")}, the Sphinx developers'
version = sphinx.__display_version__
release = version
show_authors = True
nitpicky = True
show_warning_types = True

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
epub_post_files = [
    ('usage/installation.xhtml', 'Installing Sphinx'),
    ('develop.xhtml', 'Sphinx development'),
]
epub_exclude_files = [
    '_static/opensearch.xml',
    '_static/doctools.js',
    '_static/searchtools.js',
    '_static/sphinx_highlight.js',
    '_static/basic.css',
    '_static/language_data.js',
    'search.html',
    '_static/websupport.js',
]
epub_fix_images = False
epub_max_image_width = 0
epub_show_urls = 'inline'
epub_use_index = False
epub_description = 'Sphinx documentation generator system manual'

latex_documents = [
    ('index', 'sphinx.tex', 'Sphinx Documentation', 'the Sphinx developers', 'manual', 1)
]
latex_logo = '_static/sphinx.png'
latex_elements = {
    'fontenc': r'\usepackage[LGR,X2,T1]{fontenc}',
    'passoptionstopackages': r"""
\PassOptionsToPackage{svgnames}{xcolor}
""",
    'preamble': r"""
\DeclareUnicodeCharacter{229E}{\ensuremath{\boxplus}}
\setcounter{tocdepth}{3}%    depth of what main TOC shows (3=subsubsection)
\setcounter{secnumdepth}{1}% depth of section numbering
\setlength{\tymin}{2cm}%     avoid too cramped table columns
""",
    # fix missing index entry due to RTD doing only once pdflatex after makeindex
    'printindex': r"""
\IfFileExists{\jobname.ind}
             {\footnotesize\raggedright\printindex}
             {\begin{sphinxtheindex}\end{sphinxtheindex}}
""",
}
latex_show_urls = 'footnote'
latex_use_xindy = True

linkcheck_timeout = 5
linkcheck_ignore = [
    r'^contents\.html$',  # extra generated page
    r'^\.\./contents\.html$',
    re.escape('https://gitlab.com/projects/new'),  # requires sign-in
    re.escape('https://web.libera.chat/?channel=#sphinx-doc'),
]
linkcheck_anchors_ignore_for_url = [
    # anchors in Markdown files cannot be accessed directly
    'https://github.com/Khan/style-guides/blob/master/style/python.md',
]

autodoc_member_order = 'groupwise'
autosummary_generate = False
todo_include_todos = 'READTHEDOCS' not in os.environ
extlinks = {
    'dupage': ('https://docutils.sourceforge.io/docs/ref/rst/%s.html', '%s'),
    'duref': (
        'https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html#%s',
        '%s',
    ),
    'durole': ('https://docutils.sourceforge.io/docs/ref/rst/roles.html#%s', '%s'),
    'dudir': ('https://docutils.sourceforge.io/docs/ref/rst/directives.html#%s', '%s'),
}

man_pages = [
    (
        'index',
        'sphinx-all',
        'Sphinx documentation generator system manual',
        'the Sphinx developers',
        1,
    ),
    ('man/sphinx-build', 'sphinx-build', 'Sphinx documentation generator tool', '', 1),
    (
        'man/sphinx-quickstart',
        'sphinx-quickstart',
        'Sphinx documentation template generator',
        '',
        1,
    ),
    ('man/sphinx-apidoc', 'sphinx-apidoc', 'Sphinx API doc generator tool', '', 1),
    ('man/sphinx-autogen', 'sphinx-autogen', 'Generate autodoc stub pages', '', 1),
]

texinfo_documents = [
    (
        'index',
        'sphinx',
        'Sphinx Documentation',
        'the Sphinx developers',
        'Sphinx',
        'The Sphinx documentation builder.',
        'Documentation tools',
        1,
    ),
]

intersphinx_mapping = {
    'python': ('https://docs.python.org/3/', None),
    'requests': ('https://requests.readthedocs.io/en/latest/', None),
    'readthedocs': ('https://docs.readthedocs.io/en/stable', None),
}

# Sphinx document translation with sphinx gettext feature uses these settings:
locale_dirs = ['locale/']
gettext_compact = False

nitpick_ignore = {
    (
        'cpp:class',
        'template<typename TOuter> template<typename TInner> Wrapper::Outer<TOuter>::Inner',
    ),  # NoQA: E501
    ('cpp:identifier', 'MyContainer'),
    ('js:func', 'SomeError'),
    ('js:func', 'number'),
    ('js:func', 'string'),
    ('py:attr', 'srcline'),
    ('py:class', 'Element'),  # sphinx.domains.Domain
    ('py:class', 'IndexEntry'),  # sphinx.domains.IndexEntry
    ('py:class', 'Node'),  # sphinx.domains.Domain
    ('py:class', 'NullTranslations'),  # gettext.NullTranslations
    ('py:class', 'RoleFunction'),  # sphinx.domains.Domain
    ('py:class', 'RSTState'),  # sphinx.utils.parsing.nested_parse_to_nodes
    ('py:class', 'Theme'),  # sphinx.application.TemplateBridge
    ('py:class', 'StringList'),  # sphinx.utils.parsing.nested_parse_to_nodes
    ('py:class', 'system_message'),  # sphinx.utils.docutils.SphinxDirective
    ('py:class', 'TitleGetter'),  # sphinx.domains.Domain
    ('py:class', 'XRefRole'),  # sphinx.domains.Domain
    ('py:class', 'docutils.nodes.Element'),
    ('py:class', 'docutils.nodes.Node'),
    ('py:class', 'docutils.nodes.NodeVisitor'),
    ('py:class', 'docutils.nodes.TextElement'),
    ('py:class', 'docutils.nodes.document'),
    ('py:class', 'docutils.nodes.system_message'),
    ('py:class', 'docutils.parsers.Parser'),
    ('py:class', 'docutils.parsers.rst.states.Inliner'),
    ('py:class', 'docutils.transforms.Transform'),
    ('py:class', 'nodes.NodeVisitor'),
    ('py:class', 'nodes.document'),
    ('py:class', 'nodes.reference'),
    ('py:class', 'pygments.lexer.Lexer'),
    ('py:class', 'sphinx.directives.ObjDescT'),
    ('py:class', 'sphinx.domains.IndexEntry'),
    ('py:class', 'sphinx.ext.autodoc.Documenter'),
    ('py:class', 'sphinx.errors.NoUri'),
    ('py:class', 'sphinx.roles.XRefRole'),
    ('py:class', 'sphinx.search.SearchLanguage'),
    ('py:class', 'sphinx.theming.Theme'),
    ('py:class', 'sphinxcontrib.websupport.errors.DocumentNotFoundError'),
    ('py:class', 'sphinxcontrib.websupport.errors.UserNotAuthorizedError'),
    ('py:exc', 'docutils.nodes.SkipNode'),
    ('py:exc', 'sphinx.environment.NoUri'),
    ('py:func', 'setup'),
    ('py:func', 'sphinx.util.nodes.nested_parse_with_titles'),
    # Error in sphinxcontrib.websupport.core::WebSupport.add_comment
    ('py:meth', 'get_comments'),
    ('py:mod', 'autodoc'),
    ('py:mod', 'docutils.nodes'),
    ('py:mod', 'docutils.parsers.rst.directives'),
    ('py:mod', 'sphinx.ext'),
    ('py:obj', 'sphinx.util.relative_uri'),
    ('rst:role', 'c:any'),
    ('std:confval', 'autodoc_inherit_docstring'),
    ('std:confval', 'automodule_skip_lines'),
    ('std:confval', 'autossummary_imported_members'),
    ('std:confval', 'gettext_language_team'),
    ('std:confval', 'gettext_last_translator'),
    ('std:confval', 'globaltoc_collapse'),
    ('std:confval', 'globaltoc_includehidden'),
    ('std:confval', 'globaltoc_maxdepth'),
}


# -- Extension interface -------------------------------------------------------

from sphinx import addnodes  # NoQA: E402
from sphinx.application import Sphinx  # NoQA: E402, TCH001

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
    """Linkify issue references like #123 in changelog to GitHub."""
    if docname == 'changes':
        changelog_path = os.path.join(os.path.dirname(__file__), '../CHANGES.rst')
        # this path trickery is needed because this script can
        # be invoked with different working directories:
        # * running make in docs/
        # * running tox -e docs in the repo root dir

        with open(changelog_path, encoding='utf-8') as f:
            changelog = f.read()

        def linkify(match):
            url = 'https://github.com/sphinx-doc/sphinx/issues/' + match[1]
            return f'`{match[0]} <{url}>`_'

        linkified_changelog = re.sub(r'(?:PR)?#([0-9]+)\b', linkify, changelog)

        source[0] = source[0].replace('.. include:: ../CHANGES.rst', linkified_changelog)


REDIRECT_TEMPLATE = """
<html>
    <head>
        <noscript>
            <meta http-equiv="refresh" content="0; url={{rel_url}}"/>
        </noscript>
    </head>
    <body>
        <script>
            window.location.href = '{{rel_url}}' + (window.location.search || '') + (window.location.hash || '');
        </script>
        <p>You should have been redirected.</p>
        <a href="{{rel_url}}">If not, click here to continue.</a>
    </body>
</html>
"""  # noqa: E501


def build_redirects(app: Sphinx, exception: Exception | None) -> None:
    # this is a very simple implementation of
    # https://github.com/wpilibsuite/sphinxext-rediraffe/blob/main/sphinxext/rediraffe.py
    # to re-direct some old pages to new ones
    if exception is not None or app.builder.name != 'html':
        return
    for page, rel_redirect in (
        (('development', 'overview.html'), 'index.html'),
        (('development', 'builders.html'), 'howtos/builders.html'),
        (('development', 'theming.html'), 'html_themes/index.html'),
        (('development', 'templating.html'), 'html_themes/templating.html'),
        (('development', 'tutorials', 'helloworld.html'), 'extending_syntax.html'),
        (('development', 'tutorials', 'todo.html'), 'extending_build.html'),
        (('development', 'tutorials', 'recipe.html'), 'adding_domain.html'),
    ):
        path = app.outdir.joinpath(*page)
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', encoding='utf-8') as f:
            f.write(REDIRECT_TEMPLATE.replace('{{rel_url}}', rel_redirect))


def setup(app: Sphinx) -> None:
    from sphinx.ext.autodoc import cut_lines
    from sphinx.util.docfields import GroupedField

    app.connect('autodoc-process-docstring', cut_lines(4, what=['module']))
    app.connect('source-read', linkify_issues_in_changelog)
    app.connect('build-finished', build_redirects)
    app.add_object_type(
        'confval',
        'confval',
        objname='configuration value',
        indextemplate='pair: %s; configuration value',
    )
    fdesc = GroupedField('parameter', label='Parameters', names=['param'], can_collapse=True)
    app.add_object_type(
        'event', 'event', 'pair: %s; event', parse_event, doc_field_types=[fdesc]
    )
