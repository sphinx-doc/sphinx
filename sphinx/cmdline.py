# -*- coding: utf-8 -*-
"""
    sphinx.cmdline
    ~~~~~~~~~~~~~~

    sphinx-build command-line handling.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import os
import sys
import getopt
import traceback
from os import path

from docutils.utils import SystemMessage

from sphinx import __version__
from sphinx.application import Sphinx, SphinxError
from sphinx.util import format_exception_cut_frames, save_traceback
from sphinx.util.console import darkred, nocolor, color_terminal


def usage(argv, msg=None):
    if msg:
        print >>sys.stderr, msg
        print >>sys.stderr
    print >>sys.stderr, """\
Sphinx v%s
Usage: %s [options] sourcedir outdir [filenames...]
Options: -b <builder> -- builder to use; default is html
         -a        -- write all files; default is to only write new and changed files
         -E        -- don't use a saved environment, always read all files
         -d <path> -- path for the cached environment and doctree files
                      (default: outdir/.doctrees)
         -c <path> -- path where configuration file (conf.py) is located
                      (default: same as sourcedir)
         -C        -- use no config file at all, only -D options
         -D <setting=value> -- override a setting in configuration
         -A <name=value>    -- pass a value into the templates, for HTML builder
         -N        -- do not do colored output
         -q        -- no output on stdout, just warnings on stderr
         -Q        -- no output at all, not even warnings
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
        opts, args = getopt.getopt(argv[1:], 'ab:d:c:CD:A:NEqP')
        allopts = set(opt[0] for opt in opts)
        srcdir = confdir = path.abspath(args[0])
        if not path.isdir(srcdir):
            print >>sys.stderr, 'Error: Cannot find source directory.'
            return 1
        if not path.isfile(path.join(srcdir, 'conf.py')) and \
               '-c' not in allopts and '-C' not in allopts:
            print >>sys.stderr, 'Error: Source directory doesn\'t contain conf.py file.'
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
    freshenv = use_pdb = False
    status = sys.stdout
    warning = sys.stderr
    confoverrides = {}
    htmlcontext = {}
    doctreedir = path.join(outdir, '.doctrees')
    for opt, val in opts:
        if opt == '-b':
            buildername = val
        elif opt == '-a':
            if filenames:
                usage(argv, 'Cannot combine -a option and filenames.')
                return 1
            all_files = True
        elif opt == '-d':
            doctreedir = path.abspath(val)
        elif opt == '-c':
            confdir = path.abspath(val)
            if not path.isfile(path.join(confdir, 'conf.py')):
                print >>sys.stderr, \
                      'Error: Configuration directory doesn\'t contain conf.py file.'
                return 1
        elif opt == '-C':
            confdir = None
        elif opt == '-D':
            try:
                key, val = val.split('=')
            except ValueError:
                print >>sys.stderr, \
                      'Error: -D option argument must be in the form name=value.'
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
                print >>sys.stderr, \
                      'Error: -A option argument must be in the form name=value.'
                return 1
            try:
                val = int(val)
            except ValueError:
                pass
            htmlcontext[key] = val
        elif opt == '-N':
            nocolor()
        elif opt == '-E':
            freshenv = True
        elif opt == '-q':
            status = None
        elif opt == '-Q':
            status = None
            warning = None
        elif opt == '-P':
            use_pdb = True
    confoverrides['html_context'] = htmlcontext

    try:
        app = Sphinx(srcdir, confdir, outdir, doctreedir, buildername,
                     confoverrides, status, warning, freshenv)
        app.build(all_files, filenames)
        return app.statuscode
    except KeyboardInterrupt:
        if use_pdb:
            import pdb
            print >>sys.stderr, darkred('Interrupted while building, starting debugger:')
            traceback.print_exc()
            pdb.post_mortem(sys.exc_info()[2])
        return 1
    except Exception, err:
        if use_pdb:
            import pdb
            print >>sys.stderr, darkred('Exception occurred while building, '
                                        'starting debugger:')
            traceback.print_exc()
            pdb.post_mortem(sys.exc_info()[2])
        else:
            if isinstance(err, SystemMessage):
                print >>sys.stderr, darkred('reST markup error:')
                print >>sys.stderr, err.args[0].encode('ascii', 'backslashreplace')
            elif isinstance(err, SphinxError):
                print >>sys.stderr, darkred('%s:' % err.category)
                print >>sys.stderr, err
            else:
                print >>sys.stderr, darkred('Exception occurred:')
                print >>sys.stderr, format_exception_cut_frames().rstrip()
                tbpath = save_traceback()
                print >>sys.stderr, darkred('The full traceback has been saved '
                                            'in %s, if you want to report the '
                                            'issue to the author.' % tbpath)
                print >>sys.stderr, ('Please also report this if it was a user '
                                     'error, so that a better error message '
                                     'can be provided next time.')
                print >>sys.stderr, ('Send reports to sphinx-dev@googlegroups.com. '
                                     'Thanks!')
            return 1
