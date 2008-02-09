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

from sphinx.util.console import darkgreen, purple, bold, red, nocolor


QUICKSTART_CONF = '''\
# -*- coding: utf-8 -*-
#
# %(project)s documentation build configuration file, created by
# sphinx-quickstart.py on %(now)s.
#
# This file is execfile()d with the current directory set to its containing dir.
#
# The contents of this file are pickled, so don't put values in the namespace
# that aren't pickleable (module imports are okay, they're removed automatically).
#
# All configuration values have a default value; values that are commented out
# show the default value as assigned to them.

import sys

# If your extensions are in another directory, add it here.
#sys.path.append('some/directory')

# General configuration
# ---------------------

# Add any Sphinx extension module names here, as strings. They can be extensions
# coming with Sphinx (named 'sphinx.addons.*') or your custom ones.
#extensions = []

# Add any paths that contain templates here, relative to this directory.
#templates_path = []

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

# If true, '()' will be appended to :func: etc. cross-reference text.
#add_function_parentheses = True

# If true, the current module name will be prepended to all description
# unit titles (such as .. function::).
#add_module_names = True


# Options for HTML output
# -----------------------

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
html_last_updated_fmt = '%%b %%d, %%Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Content template for the index page, filename relative to this file.
#html_index = ''

# Custom sidebar templates, maps page names to filenames relative to this file.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# filenames relative to this file.
#html_additional_pages = {}

# If true, the reST sources are included in the HTML build as _sources/<name>.
#html_copy_source = True

# Output file base name for HTML help builder.
htmlhelp_basename = '%(project)sdoc'


# Options for LaTeX output
# ------------------------

# The paper size ('letter' or 'a4').
#latex_paper_size = 'letter'

# The font size ('10pt', '11pt' or '12pt').
#latex_font_size = '10pt'

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, document class [howto/manual]).
#latex_documents = []

# Additional stuff for the LaTeX preamble.
#latex_preamble = '

# Documents to append as an appendix to all manuals.
#latex_appendices = []
'''

def is_path(x):
    """Please enter an existing path name."""
    return path.isdir(x)

def nonempty(x):
    """Please enter some text."""
    return len(x)

def suffix(x):
    """Please enter a file suffix, e.g. '.rst' or '.txt'."""
    return x[0:1] == '.' and len(x) > 1


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
This tool will create "src" and "build" folders in this path, which
must be an existing directory.'''
    do_prompt(d, 'path', 'Root path for the documentation', '.', is_path)
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
    do_prompt(d, 'master', 'Name of your master document (without suffix)', 'index')

    d['year'] = time.strftime('%Y')
    d['now'] = time.asctime()

    os.mkdir(path.join(d['path'], 'src'))
    os.mkdir(path.join(d['path'], 'build'))

    f = open(path.join(d['path'], 'src', 'conf.py'), 'w')
    f.write(QUICKSTART_CONF % d)
    f.close()

    masterfile = path.join(d['path'], 'src', d['master'] + d['suffix'])

    print
    print bold('Finished: An initial directory structure has been created.')
    print '''
You should now create your master file %s and other documentation
sources. Use the sphinx-build.py script to build the docs.
''' % (masterfile)


def main(argv=sys.argv):
    try:
        return inner_main(argv)
    except (KeyboardInterrupt, EOFError):
        print
        print '[Interrupted.]'
        return

