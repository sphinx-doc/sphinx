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

from sphinx.util import format_exception_cut_frames, save_traceback
from sphinx.util.console import darkred, nocolor, color_terminal

__revision__ = '$Revision$'
__version__ = '0.5'
__released__ = '0.5 (hg)'


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
         -D <setting=value> -- override a setting in configuration
         -A <name=value>    -- pass a value into the templates, for HTML builder
         -N        -- do not do colored output
         -q        -- no output on stdout, just warnings on stderr
         -P        -- run Pdb on exception
Modi:
* without -a and without filenames, write new and changed files.
* with -a, write all files.
* with filenames, write these.""" % (__version__, argv[0])


def main(argv=sys.argv):
    # delay-import these to be able to get sphinx.__version__ from setup.py
    # even without docutils installed
    from sphinx.application import Sphinx, SphinxError
    from docutils.utils import SystemMessage

    if not sys.stdout.isatty() or not color_terminal():
        # Windows' poor cmd box doesn't understand ANSI sequences
        nocolor()

    try:
        opts, args = getopt.getopt(argv[1:], 'ab:d:c:D:A:NEqP')
        srcdir = confdir = path.abspath(args[0])
        if not path.isdir(srcdir):
            print >>sys.stderr, 'Error: Cannot find source directory.'
            return 1
        if not path.isfile(path.join(srcdir, 'conf.py')) and \
               '-c' not in (opt[0] for opt in opts):
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
            status = StringIO()
        elif opt == '-P':
            use_pdb = True
    confoverrides['html_context'] = htmlcontext

    try:
        app = Sphinx(srcdir, confdir, outdir, doctreedir, buildername,
                     confoverrides, status, sys.stderr, freshenv)
        app.build(all_files, filenames)
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


if __name__ == '__main__':
    sys.exit(main(sys.argv))
