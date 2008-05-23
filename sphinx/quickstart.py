# -*- coding: utf-8 -*-
"""
    sphinx.quickstart
    ~~~~~~~~~~~~~~~~~

    Quickly setup documentation source to work with Sphinx.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import sys, os, time
from os import path

from sphinx.util import make_filename
from sphinx.util.console import purple, bold, red, nocolor


QUICKSTART_CONF = '''\
# -*- coding: utf-8 -*-
#
# %(project)s documentation build configuration file, created by
# sphinx-quickstart on %(now)s.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#
# All configuration values have a default value; values that are commented out
# serve to show the default value.

import sys, os

# If your extensions are in another directory, add it here. If the directory
# is relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
#sys.path.append(os.path.abspath('some/directory'))

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
#extensions = []

# Add any paths that contain templates here, relative to this directory.
templates_path = ['%(dot)stemplates']

# The suffix of source filenames.
source_suffix = '%(suffix)s'

# The master toctree document.
master_doc = '%(master)s'

# General substitutions.
project = %(project)r
copyright = '%(year)s, %(author)s'

# The default replacements for |version| and |release|, also used in various
# other places throughout the built documents.
#
# The short X.Y version.
version = '%(version)s'
# The full version, including alpha/beta/rc tags.
release = '%(release)s'

# There are two options for replacing |today|: either, you set today to some
# non-false value, then it is used:
#today = ''
# Else, today_fmt is used as the format for a strftime call.
today_fmt = '%%B %%d, %%Y'

# List of documents that shouldn't be included in the build.
#unused_docs = []

# List of directories, relative to source directories, that shouldn't be searched
# for source files.
#exclude_dirs = []

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True

# If true, sectionauthor and moduleauthor directives will be shown in the
# output. They are ignored by default.
#show_authors = False

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'


# Options for HTML output
# -----------------------

# The style sheet to use for HTML and HTML Help pages. A file of that name
# must exist either in Sphinx' static/ path, or in one of the custom paths
# given in html_static_path.
html_style = 'default.css'

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# The name of an image file (within the static path) to place at the top of
# the sidebar.
#html_logo = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['%(dot)sstatic']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%%b %%d, %%Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
#html_use_modindex = True

# If true, the reST sources are included in the HTML build as _sources/<name>.
#html_copy_source = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# If nonempty, this is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = ''

# Output file base name for HTML help builder.
htmlhelp_basename = '%(project_fn)sdoc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
latex_documents = [
  ('%(master)s', '%(project_fn)s.tex', '%(project)s Documentation', '%(author)s', 'manual'),
]

# The name of an image file (relative to this directory) to place at the top of
# the title page.
#latex_logo = None

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
#latex_use_parts = False

# Additional stuff for the LaTeX preamble.
#latex_preamble = ''

# Documents to append as an appendix to all manuals.
#latex_appendices = []

# If false, no module index is generated.
#latex_use_modindex = True
'''

MASTER_FILE = '''\
.. %(project)s documentation master file, created by sphinx-quickstart on %(now)s.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to %(project)s's documentation!
===========%(underline)s=================

Contents:

.. toctree::
   :maxdepth: 2

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

'''

MAKEFILE = '''\
# Makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
PAPER         =

# Internal variables.
PAPEROPT_a4     = -D latex_paper_size=a4
PAPEROPT_letter = -D latex_paper_size=letter
ALLSPHINXOPTS   = -d %(rbuilddir)s/doctrees $(PAPEROPT_$(PAPER)) $(SPHINXOPTS) %(rsrcdir)s

.PHONY: help clean html web pickle htmlhelp latex changes linkcheck

help:
\t@echo "Please use \\`make <target>' where <target> is one of"
\t@echo "  html      to make standalone HTML files"
\t@echo "  pickle    to make pickle files (usable by e.g. sphinx-web)"
\t@echo "  htmlhelp  to make HTML files and a HTML help project"
\t@echo "  latex     to make LaTeX files, you can set PAPER=a4 or PAPER=letter"
\t@echo "  changes   to make an overview over all changed/added/deprecated items"
\t@echo "  linkcheck to check all external links for integrity"

clean:
\t-rm -rf %(rbuilddir)s/*

html:
\tmkdir -p %(rbuilddir)s/html %(rbuilddir)s/doctrees
\t$(SPHINXBUILD) -b html $(ALLSPHINXOPTS) %(rbuilddir)s/html
\t@echo
\t@echo "Build finished. The HTML pages are in %(rbuilddir)s/html."

pickle:
\tmkdir -p %(rbuilddir)s/pickle %(rbuilddir)s/doctrees
\t$(SPHINXBUILD) -b pickle $(ALLSPHINXOPTS) %(rbuilddir)s/pickle
\t@echo
\t@echo "Build finished; now you can process the pickle files or run"
\t@echo "  sphinx-web %(rbuilddir)s/pickle"
\t@echo "to start the sphinx-web server."

web: pickle

htmlhelp:
\tmkdir -p %(rbuilddir)s/htmlhelp %(rbuilddir)s/doctrees
\t$(SPHINXBUILD) -b htmlhelp $(ALLSPHINXOPTS) %(rbuilddir)s/htmlhelp
\t@echo
\t@echo "Build finished; now you can run HTML Help Workshop with the" \\
\t      ".hhp project file in %(rbuilddir)s/htmlhelp."

latex:
\tmkdir -p %(rbuilddir)s/latex %(rbuilddir)s/doctrees
\t$(SPHINXBUILD) -b latex $(ALLSPHINXOPTS) %(rbuilddir)s/latex
\t@echo
\t@echo "Build finished; the LaTeX files are in %(rbuilddir)s/latex."
\t@echo "Run \\`make all-pdf' or \\`make all-ps' in that directory to" \\
\t      "run these through (pdf)latex."

changes:
\tmkdir -p %(rbuilddir)s/changes %(rbuilddir)s/doctrees
\t$(SPHINXBUILD) -b changes $(ALLSPHINXOPTS) %(rbuilddir)s/changes
\t@echo
\t@echo "The overview file is in %(rbuilddir)s/changes."

linkcheck:
\tmkdir -p %(rbuilddir)s/linkcheck %(rbuilddir)s/doctrees
\t$(SPHINXBUILD) -b linkcheck $(ALLSPHINXOPTS) %(rbuilddir)s/linkcheck
\t@echo
\t@echo "Link check complete; look for any errors in the above output " \\
\t      "or in %(rbuilddir)s/linkcheck/output.txt."
'''


def mkdir_p(dir):
    if path.isdir(dir):
        return
    os.makedirs(dir)


def is_path(x):
    """Please enter a valid path name."""
    return path.isdir(x) or not path.exists(x)

def nonempty(x):
    """Please enter some text."""
    return len(x)

def choice(*l):
    def val(x):
        return x in l
    val.__doc__ = 'Please enter one of %s.' % ', '.join(l)
    return val

def boolean(x):
    """Please enter either 'y' or 'n'."""
    return x.upper() in ('Y', 'YES', 'N', 'NO')

def suffix(x):
    """Please enter a file suffix, e.g. '.rst' or '.txt'."""
    return x[0:1] == '.' and len(x) > 1

def ok(x):
    return True


def do_prompt(d, key, text, default=None, validator=nonempty):
    while True:
        if default:
            prompt = purple('> %s [%s]: ' % (text, default))
        else:
            prompt = purple('> ' + text + ': ')
        x = raw_input(prompt)
        if default and not x:
            x = default
        if validator and not validator(x):
            print red(" * " + validator.__doc__)
            continue
        break
    d[key] = x


def inner_main(args):
    d = {}

    if os.name == 'nt' or not sys.stdout.isatty():
        nocolor()

    print bold('Welcome to the Sphinx quickstart utility.')
    print '''
Please enter values for the following settings (just press Enter to
accept a default value, if one is given in brackets).'''

    print '''
Enter the root path for documentation.'''
    do_prompt(d, 'path', 'Root path for the documentation', '.', is_path)
    print '''
You have two options for placing the build directory for Sphinx output.
Either, you use a directory ".build" within the root path, or you separate
"source" and "build" directories within the root path.'''
    do_prompt(d, 'sep', 'Separate source and build directories (y/n)', 'n',
              boolean)
    print '''
Inside the root directory, two more directories will be created; ".templates"
for custom HTML templates and ".static" for custom stylesheets and other
static files. Since the leading dot may be inconvenient for Windows users,
you can enter another prefix (such as "_") to replace the dot.'''
    do_prompt(d, 'dot', 'Name prefix for templates and static dir', '.', ok)

    print '''
The project name will occur in several places in the built documentation.'''
    do_prompt(d, 'project', 'Project name')
    do_prompt(d, 'author', 'Author name(s)')
    print '''
Sphinx has the notion of a "version" and a "release" for the
software. Each version can have multiple releases. For example, for
Python the version is something like 2.5 or 3.0, while the release is
something like 2.5.1 or 3.0a1.  If you don't need this dual structure,
just set both to the same value.'''
    do_prompt(d, 'version', 'Project version')
    do_prompt(d, 'release', 'Project release', d['version'])
    print '''
The file name suffix for source files. Commonly, this is either ".txt"
or ".rst".  Only files with this suffix are considered documents.'''
    do_prompt(d, 'suffix', 'Source file suffix', '.rst', suffix)
    print '''
One document is special in that it is considered the top node of the
"contents tree", that is, it is the root of the hierarchical structure
of the documents. Normally, this is "index", but if your "index"
document is a custom template, you can also set this to another filename.'''
    do_prompt(d, 'master', 'Name of your master document (without suffix)',
              'index')
    print '''
If you are under Unix, a Makefile can be generated for you so that you
only have to run e.g. `make html' instead of invoking sphinx-build
directly.'''
    do_prompt(d, 'makefile', 'Create Makefile? (y/n)',
              os.name == 'posix' and 'y' or 'n', boolean)

    d['project_fn'] = make_filename(d['project'])
    d['year'] = time.strftime('%Y')
    d['now'] = time.asctime()
    d['underline'] = len(d['project']) * '='

    if not path.isdir(d['path']):
        mkdir_p(d['path'])

    separate = d['sep'].upper() in ('Y', 'YES')
    srcdir = separate and path.join(d['path'], 'source') or d['path']

    mkdir_p(srcdir)
    if separate:
        builddir = path.join(d['path'], 'build')
    else:
        builddir = path.join(srcdir, d['dot'] + 'build')
    mkdir_p(builddir)
    mkdir_p(path.join(srcdir, d['dot'] + 'templates'))
    mkdir_p(path.join(srcdir, d['dot'] + 'static'))

    f = open(path.join(srcdir, 'conf.py'), 'w')
    f.write(QUICKSTART_CONF % d)
    f.close()

    masterfile = path.join(srcdir, d['master'] + d['suffix'])
    f = open(masterfile, 'w')
    f.write(MASTER_FILE % d)
    f.close()

    create_makefile = d['makefile'].upper() in ('Y', 'YES')
    if create_makefile:
        d['rsrcdir'] = separate and 'source' or '.'
        d['rbuilddir'] = separate and 'build' or d['dot'] + 'build'
        f = open(path.join(d['path'], 'Makefile'), 'w')
        f.write(MAKEFILE % d)
        f.close()

    print
    print bold('Finished: An initial directory structure has been created.')
    print '''
You should now populate your master file %s and create other documentation
source files. Use the sphinx-build script to build the docs, like so:
''' % masterfile + (create_makefile and '''
   make <builder>
''' or '''
   sphinx-build -b <builder> %s %s
''' % (srcdir, builddir))


def main(argv=sys.argv):
    try:
        return inner_main(argv)
    except (KeyboardInterrupt, EOFError):
        print
        print '[Interrupted.]'
        return

