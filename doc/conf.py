# -*- coding: utf-8 -*-
#
# Sphinx documentation build configuration file

import sys, os, re

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.addons.*') or your custom ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx.ext.todo',
              'sphinx.ext.autosummary']

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix of source filenames.
source_suffix = '.rst'

# The master toctree document.
master_doc = 'contents'

# General substitutions.
project = 'Sphinx'
copyright = '2007-2010, Georg Brandl'

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
import sphinx
version = sphinx.__released__
release = version

# Show author directives in the output.
show_authors = True

# The HTML template theme.
html_theme = 'sphinxdoc'

# A list of ignored prefixes names for module index sorting.
modindex_common_prefix = ['sphinx.']

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%b %d, %Y'

# Content template for the index page.
html_index = 'index.html'

# Custom sidebar templates, maps page names to templates.
html_sidebars = {'index': 'indexsidebar.html'}

# Additional templates that should be rendered to pages, maps page names to
# templates.
html_additional_pages = {'index': 'index.html'}

# Generate an OpenSearch description with that URL as the base.
html_use_opensearch = 'http://sphinx.pocoo.org'

# Output file base name for HTML help builder.
htmlhelp_basename = 'Sphinxdoc'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass [howto/manual]).
latex_documents = [('contents', 'sphinx.tex', 'Sphinx Documentation',
                    'Georg Brandl', 'manual', 1)]

# Add our logo to the LaTeX file.
latex_logo = '_static/sphinx.png'

# Additional stuff for the LaTeX preamble.
latex_elements = {
    'fontpkg': '\\usepackage{palatino}'
}

# Put TODOs into the output.
todo_include_todos = True


# -- Extension interface -------------------------------------------------------

from sphinx import addnodes

dir_sig_re = re.compile(r'\.\. ([^:]+)::(.*)$')

def parse_directive(env, sig, signode):
    if not sig.startswith('.'):
        dec_sig = '.. %s::' % sig
        signode += addnodes.desc_name(dec_sig, dec_sig)
        return sig
    m = dir_sig_re.match(sig)
    if not m:
        signode += addnodes.desc_name(sig, sig)
        return sig
    name, args = m.groups()
    dec_name = '.. %s::' % name
    signode += addnodes.desc_name(dec_name, dec_name)
    signode += addnodes.desc_addname(args, args)
    return name


def parse_role(env, sig, signode):
    signode += addnodes.desc_name(':%s:' % sig, ':%s:' % sig)
    return sig


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
    app.connect('autodoc-process-docstring', cut_lines(4, what=['module']))
    app.add_description_unit('directive', 'dir', 'pair: %s; directive',
                             parse_directive)
    app.add_description_unit('role', 'role', 'pair: %s; role', parse_role)
    app.add_description_unit('confval', 'confval',
                             'pair: %s; configuration value')
    app.add_description_unit('event', 'event', 'pair: %s; event', parse_event)
