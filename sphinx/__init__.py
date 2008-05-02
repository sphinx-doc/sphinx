# -*- coding: utf-8 -*-
"""
    Sphinx
    ~~~~~~

    The Sphinx documentation toolchain.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import os
import sys
import getopt
import traceback
from os import path
from cStringIO import StringIO

from docutils.utils import SystemMessage

from sphinx.util import format_exception_cut_frames, save_traceback
from sphinx.application import Sphinx
from sphinx.util.console import darkred, nocolor

__revision__ = '$Revision$'
__version__ = '0.2.1'


def usage(argv, msg=None):
    if msg:
        print >>sys.stderr, msg
        print >>sys.stderr
    print >>sys.stderr, """\
Sphinx v%s
Usage: %s [options] sourcedir outdir [filenames...]"
Options: -b <builder> -- builder to use; default is html
         -a        -- write all files; default is to only write new and changed files
         -E        -- don't use a saved environment, always read all files
         -d <path> -- path for the cached environment and doctree files
                      (default outdir/.doctrees)
         -D <setting=value> -- override a setting in sourcedir/conf.py
         -N        -- do not do colored output
         -q        -- no output on stdout, just warnings on stderr
         -P        -- run Pdb on exception
Modi:
* without -a and without filenames, write new and changed files.
* with -a, write all files.
* with filenames, write these.""" % (__version__, argv[0])


def main(argv=sys.argv):
    if not sys.stdout.isatty() or sys.platform == 'win32':
        # Windows' poor cmd box doesn't understand ANSI sequences
        nocolor()

    try:
        opts, args = getopt.getopt(argv[1:], 'ab:d:D:NEqP')
        srcdir = path.abspath(args[0])
        if not path.isdir(srcdir):
            print >>sys.stderr, 'Error: Cannot find source directory.'
            return 1
        if not path.isfile(path.join(srcdir, 'conf.py')):
            print >>sys.stderr, 'Error: Source directory doesn\'t contain conf.py file.'
            return 1
        outdir = path.abspath(args[1])
        if not path.isdir(outdir):
            print >>sys.stderr, 'Error: Cannot find output directory.'
            return 1
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
    confoverrides = {}
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
            doctreedir = val
        elif opt == '-D':
            key, val = val.split('=')
            try:
                val = int(val)
            except: pass
            confoverrides[key] = val
        elif opt == '-N':
            nocolor()
        elif opt == '-E':
            freshenv = True
        elif opt == '-q':
            status = StringIO()
        elif opt == '-P':
            use_pdb = True

    try:
        app = Sphinx(srcdir, outdir, doctreedir, buildername,
                     confoverrides, status, sys.stderr, freshenv)
        if not app.builder:
            return 1

        if all_files:
            app.builder.build_all()
        elif filenames:
            app.builder.build_specific(filenames)
        else:
            app.builder.build_update()
    except KeyboardInterrupt:
        # catches BaseExceptions in 2.5 -- SystemExit, KeyboardInterrupt
        return 1
    except SystemExit:
        return 0
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
                print >>sys.stderr, str(err)
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
                print >>sys.stderr, 'Send reports to sphinx-dev@googlegroups.com. Thanks!'
            return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
