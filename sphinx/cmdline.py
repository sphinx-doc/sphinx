# -*- coding: utf-8 -*-
"""
    sphinx.cmdline
    ~~~~~~~~~~~~~~

    sphinx-build command-line handling.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys
import getopt
import traceback
from os import path

from docutils.utils import SystemMessage

from sphinx import __version__
from sphinx.errors import SphinxError
from sphinx.application import Sphinx
from sphinx.util import Tee, format_exception_cut_frames, save_traceback
from sphinx.util.console import darkred, nocolor, color_terminal


def usage(argv, msg=None):
    if msg:
        print >>sys.stderr, msg
        print >>sys.stderr
    print >>sys.stderr, """\
Sphinx v%s
Usage: %s [options] sourcedir outdir [filenames...]
Options: -b <builder> -- builder to use; default is html
         -a        -- write all files; default is to only write \
new and changed files
         -E        -- don't use a saved environment, always read all files
         -t <tag>  -- include "only" blocks with <tag>
         -d <path> -- path for the cached environment and doctree files
                      (default: outdir/.doctrees)
         -c <path> -- path where configuration file (conf.py) is located
                      (default: same as sourcedir)
         -C        -- use no config file at all, only -D options
         -D <setting=value> -- override a setting in configuration
         -A <name=value>    -- pass a value into the templates, for HTML builder
         -g <path> -- auto-generate docs with sphinx.ext.autosummary
                      for autosummary directives in sources found in path
         -N        -- do not do colored output
         -q        -- no output on stdout, just warnings on stderr
         -Q        -- no output at all, not even warnings
         -w <file> -- write warnings (and errors) to given file
         -W        -- turn warnings into errors
         -P        -- run Pdb on exception
Modi:
* without -a and without filenames, write new and changed files.
* with -a, write all files.
* with filenames, write these.""" % (__version__, argv[0])


def main(argv):
    if not sys.stdout.isatty() or not color_terminal():
        # Windows' poor cmd box doesn't understand ANSI sequences
        nocolor()

    try:
        opts, args = getopt.getopt(argv[1:], 'ab:t:d:c:CD:A:g:NEqQWw:P')
        allopts = set(opt[0] for opt in opts)
        srcdir = confdir = path.abspath(args[0])
        if not path.isdir(srcdir):
            print >>sys.stderr, 'Error: Cannot find source directory.'
            return 1
        if not path.isfile(path.join(srcdir, 'conf.py')) and \
               '-c' not in allopts and '-C' not in allopts:
            print >>sys.stderr, ('Error: Source directory doesn\'t '
                                 'contain conf.py file.')
            return 1
        outdir = path.abspath(args[1])
        if not path.isdir(outdir):
            print >>sys.stderr, 'Making output directory...'
            os.makedirs(outdir)
    except (IndexError, getopt.error):
        usage(argv)
        return 1

    filenames = args[2:]
    err = 0
    for filename in filenames:
        if not path.isfile(filename):
            print >>sys.stderr, 'Cannot find file %r.' % filename
            err = 1
    if err:
        return 1

    buildername = all_files = None
    freshenv = warningiserror = use_pdb = False
    status = sys.stdout
    warning = sys.stderr
    error = sys.stderr
    warnfile = None
    confoverrides = {}
    htmlcontext = {}
    tags = []
    doctreedir = path.join(outdir, '.doctrees')
    for opt, val in opts:
        if opt == '-b':
            buildername = val
        elif opt == '-a':
            if filenames:
                usage(argv, 'Cannot combine -a option and filenames.')
                return 1
            all_files = True
        elif opt == '-t':
            tags.append(val)
        elif opt == '-d':
            doctreedir = path.abspath(val)
        elif opt == '-c':
            confdir = path.abspath(val)
            if not path.isfile(path.join(confdir, 'conf.py')):
                print >>sys.stderr, ('Error: Configuration directory '
                                     'doesn\'t contain conf.py file.')
                return 1
        elif opt == '-C':
            confdir = None
        elif opt == '-D':
            try:
                key, val = val.split('=')
            except ValueError:
                print >>sys.stderr, ('Error: -D option argument must be '
                                     'in the form name=value.')
                return 1
            try:
                val = int(val)
            except ValueError:
                pass
            confoverrides[key] = val
        elif opt == '-A':
            try:
                key, val = val.split('=')
            except ValueError:
                print >>sys.stderr, ('Error: -A option argument must be '
                                     'in the form name=value.')
                return 1
            try:
                val = int(val)
            except ValueError:
                pass
            htmlcontext[key] = val
        elif opt == '-g':
            # XXX XXX XXX
            source_filenames = [path.join(srcdir, f)
                                for f in os.listdir(srcdir) if f.endswith('.rst')]
            if val is None:
                print >>sys.stderr, \
                      'Error: you must provide a destination directory ' \
                      'for autodoc generation.'
                return 1
            p = path.abspath(val)
            from sphinx.ext.autosummary.generate import generate_autosummary_docs
            generate_autosummary_docs(source_filenames, p)
        elif opt == '-N':
            nocolor()
        elif opt == '-E':
            freshenv = True
        elif opt == '-q':
            status = None
        elif opt == '-Q':
            status = None
            warning = None
        elif opt == '-W':
            warningiserror = True
        elif opt == '-w':
            warnfile = val
        elif opt == '-P':
            use_pdb = True
    confoverrides['html_context'] = htmlcontext

    if warning and warnfile:
        warnfp = open(warnfile, 'w')
        warning = Tee(warning, warnfp)
        error = warning

    try:
        app = Sphinx(srcdir, confdir, outdir, doctreedir, buildername,
                     confoverrides, status, warning, freshenv,
                     warningiserror, tags)
        app.build(all_files, filenames)
        return app.statuscode
    except KeyboardInterrupt:
        if use_pdb:
            import pdb
            print >>error, darkred('Interrupted while building, '
                                   'starting debugger:')
            traceback.print_exc()
            pdb.post_mortem(sys.exc_info()[2])
        return 1
    except Exception, err:
        if use_pdb:
            import pdb
            print >>error, darkred('Exception occurred while building, '
                                   'starting debugger:')
            traceback.print_exc()
            pdb.post_mortem(sys.exc_info()[2])
        else:
            if isinstance(err, SystemMessage):
                print >>error, darkred('reST markup error:')
                print >>error, err.args[0].encode('ascii', 'backslashreplace')
            elif isinstance(err, SphinxError):
                print >>error, darkred('%s:' % err.category)
                print >>error, err
            else:
                print >>error, darkred('Exception occurred:')
                print >>error, format_exception_cut_frames().rstrip()
                tbpath = save_traceback()
                print >>error, darkred('The full traceback has been saved '
                                       'in %s, if you want to report the '
                                       'issue to the author.' % tbpath)
                print >>error, ('Please also report this if it was a user '
                                'error, so that a better error message '
                                'can be provided next time.')
                print >>error, ('Send reports to sphinx-dev@googlegroups.com. '
                                'Thanks!')
            return 1
