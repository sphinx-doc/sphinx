# -*- coding: utf-8 -*-
"""
    sphinx.make_mode
    ~~~~~~~~~~~~~~~~

    sphinx-build -M command-line handling.

    This replaces the old, platform-dependent and once-generated content
    of Makefile / make.bat.

    This is in its own module so that importing it is fast.  It should not
    import the main Sphinx modules (like sphinx.applications, sphinx.builders).

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys
import shutil
from os import path
from subprocess import call

import sphinx
from sphinx.util.console import bold, blue

proj_name = os.getenv('SPHINXPROJ', '<project>')

def build_clean(builddir, opts):
    if not path.exists(builddir):
        return
    elif not path.isdir(builddir):
        print "Error: %r is not a directory!" % builddir
        return 1
    print "removing everything under %r..." % builddir
    for item in os.listdir(builddir):
        shutil.rmtree(path.join(builddir, item))

BUILDERS = [
    ("",      "html",      "to make standalone HTML files"),
    ("",      "dirhtml",   "to make HTML files named index.html in directories"),
    ("",      "singlehtml","to make a single large HTML file"),
    ("",      "pickle",    "to make pickle files"),
    ("",      "json",      "to make JSON files"),
    ("",      "htmlhelp",  "to make HTML files and a HTML help project"),
    ("",      "qthelp",    "to make HTML files and a qthelp project"),
    ("",      "devhelp",   "to make HTML files and a Devhelp project"),
    ("",      "epub",      "to make an epub"),
    ("",      "latex",     "to make LaTeX files, you can set PAPER=a4 or PAPER=letter"),
    ("posix", "latexpdf",  "to make LaTeX files and run them through pdflatex"),
    ("posix", "latexpdfja","to make LaTeX files and run them through platex/dvipdfmx"),
    ("",      "text",      "to make text files"),
    ("",      "man",       "to make manual pages"),
    ("",      "texinfo",   "to make Texinfo files"),
    ("posix", "info",      "to make Texinfo files and run them through makeinfo"),
    ("",      "gettext",   "to make PO message catalogs"),
    ("",      "changes",   "to make an overview of all changed/added/deprecated items"),
    ("",      "xml",       "to make Docutils-native XML files"),
    ("",      "pseudoxml", "to make pseudoxml-XML files for display purposes"),
    ("",      "linkcheck", "to check all external links for integrity"),
    ("",      "doctest",   "to run all doctests embedded in the documentation (if enabled)"),
    ("",      "coverage",  "to run coverage check of the documentation (if enabled)"),
]

def build_help(builddir, opts):
    print bold("Sphinx v%s" % sphinx.__version__)
    print "Please use `make %s' where %s is one of" % ((blue('target'),)*2)
    for osname, bname, description in BUILDERS:
        if not osname or os.name == osname:
            print '  %s  %s' % (blue(bname.ljust(10)), description)


def build_html(builddir, opts):
    if run_generic_build('html', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The HTML pages are in %s.' % path.join(builddir, 'html')

def build_dirhtml(builddir, opts):
    if run_generic_build('dirhtml', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The HTML pages are in %s.' % path.join(builddir, 'dirhtml')

def build_singlehtml(builddir, opts):
    if run_generic_build('singlehtml', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The HTML page is in %s.' % path.join(builddir, 'singlehtml')

def build_pickle(builddir, opts):
    if run_generic_build('pickle', builddir, opts) > 0:
        return 1
    print
    print 'Build finished; now you can process the pickle files.'

def build_json(builddir, opts):
    if run_generic_build('json', builddir, opts) > 0:
        return 1
    print
    print 'Build finished; now you can process the JSON files.'

def build_htmlhelp(builddir, opts):
    if run_generic_build('htmlhelp', builddir, opts) > 0:
        return 1
    print
    print ('Build finished; now you can run HTML Help Workshop with the '
           '.hhp project file in %s.') % path.join(builddir, 'htmlhelp')

def build_qthelp(builddir, opts):
    if run_generic_build('qthelp', builddir, opts) > 0:
        return 1
    print
    print ('Build finished; now you can run "qcollectiongenerator" with the '
           '.qhcp project file in %s, like this:') % path.join(builddir, 'qthelp')
    print '$ qcollectiongenerator %s.qhcp' % path.join(builddir, 'qthelp', proj_name)
    print 'To view the help file:'
    print '$ assistant -collectionFile %s.qhc' % path.join(builddir, 'qthelp', proj_name)

def build_devhelp(builddir, opts):
    if run_generic_build('devhelp', builddir, opts) > 0:
        return 1
    print
    print "Build finished."
    print "To view the help file:"
    print "$ mkdir -p $HOME/.local/share/devhelp/" + proj_name
    print "$ ln -s %s $HOME/.local/share/devhelp/%s" % \
        (path.join(builddir, 'devhelp'), proj_name)
    print "$ devhelp"

def build_epub(builddir, opts):
    if run_generic_build('epub', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The ePub file is in %s.' % path.join(builddir, 'epub')

def build_latex(builddir, opts):
    if run_generic_build('latex', builddir, opts) > 0:
        return 1
    print "Build finished; the LaTeX files are in %s." % path.join(builddir, 'latex')
    if os.name == 'posix':
        print "Run `make' in that directory to run these through (pdf)latex"
        print "(use `make latexpdf' here to do that automatically)."

def build_latexpdf(builddir, opts):
    if run_generic_build('latex', builddir, opts) > 0:
        return 1
    os.system('make -C %s all-pdf' % path.join(builddir, 'latex'))

def build_latexpdfja(builddir, opts):
    if run_generic_build('latex', builddir, opts) > 0:
        return 1
    os.system('make -C %s all-pdf-ja' % path.join(builddir, 'latex'))

def build_text(builddir, opts):
    if run_generic_build('text', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The text files are in %s.' % path.join(builddir, 'text')

def build_texinfo(builddir, opts):
    if run_generic_build('texinfo', builddir, opts) > 0:
        return 1
    print "Build finished; the Texinfo files are in %s." % path.join(builddir, 'texinfo')
    if os.name == 'posix':
        print "Run `make' in that directory to run these through makeinfo"
        print "(use `make info' here to do that automatically)."

def build_info(builddir, opts):
    if run_generic_build('texinfo', builddir, opts) > 0:
        return 1
    os.system('make -C %s info' % path.join(builddir, 'texinfo'))

def build_gettext(builddir, opts):
    dtdir = path.join(builddir, 'gettext', '.doctrees')
    if run_generic_build('gettext', builddir, opts, doctreedir=dtdir) > 0:
        return 1
    print
    print 'Build finished. The message catalogs are in %s.' % path.join(builddir, 'gettext')

def build_changes(builddir, opts):
    if run_generic_build('changes', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The overview file is in %s.' % path.join(builddir, 'changes')

def build_linkcheck(builddir, opts):
    res = run_generic_build('linkcheck', builddir, opts)
    print
    print ('Link check complete; look for any errors in the above output '
           'or in %s.') % path.join(builddir, 'linkcheck', 'output.txt')
    return res

def build_doctest(builddir, opts):
    res = run_generic_build('doctest', builddir, opts)
    print ("Testing of doctests in the sources finished, look at the "
           "results in %s." % path.join(builddir, 'doctest', 'output.txt'))
    return res

def build_coverage(builddir, opts):
    if run_generic_build('coverage', builddir, opts) > 0:
        print "Has the coverage extension been enabled?"
        return 1
    print
    print ("Testing of coverage in the sources finished, look at the "
           "results in %s." % path.join(builddir, 'coverage'))

def build_xml(builddir, opts):
    if run_generic_build('xml', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The XML files are in %s.' % path.join(builddir, 'xml')

def build_pseudoxml(builddir, opts):
    if run_generic_build('pseudoxml', builddir, opts) > 0:
        return 1
    print
    print 'Build finished. The pseudo-XML files are in %s.' % path.join(builddir, 'pseudoxml')


def run_generic_build(builder, builddir, opts, doctreedir=None):
    # compatibility with old Makefile
    papersize = os.getenv('PAPER', '')
    if papersize in ('a4', 'letter'):
        opts.extend(['-D', 'latex_paper_size=' + papersize])
    if doctreedir is None:
        doctreedir = path.join(builddir, 'doctrees')
    return call([sys.executable, sys.argv[0], '-b', builder,
                 '-d', doctreedir, '.', path.join(builddir, builder)] + opts)


def run_make_mode(args):
    if len(args) < 2:
        print >>sys.stderr, ('Error: at least two arguments (builder, build '
                             'dir) are required.')
        return 1
    run_method = 'build_' + args[0]
    if run_method in globals():
        return globals()[run_method](args[1], args[2:])
    return run_generic_build(args[0], args[1], args[2:])
