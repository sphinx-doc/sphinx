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
from os import path
from cStringIO import StringIO

from sphinx.config import Config, ConfigError
from sphinx.builder import builders
from sphinx.extension import EventManager
from sphinx.util.console import nocolor

__version__ = '$Revision: 5369 $'[11:-2]


def init_builder(buildername, srcdirname, outdirname, doctreedir,
                 confoverrides, status, warning=sys.stderr, freshenv=False):
    # read config
    config = Config(srcdirname, 'conf.py')
    if confoverrides:
        for key, val in confoverrides.items():
            setattr(config, key, val)

    # extensibility
    events = EventManager()
    for extension in config.extensions:
        try:
            mod = __import__(extension, None, None, ['setup'])
        except ImportError, err:
            raise ConfigError('Could not import extension %s' % module, err)
        if hasattr(mod, 'setup'):
            mod.setup(events, builders)

    if buildername not in builders:
        print >>warning, 'Builder name %s not registered' % buildername
        return None

    if buildername is None:
        print >>status, 'No builder selected, using default: html'
        buildername = 'html'

    builderclass = builders[buildername]
    builder = builderclass(srcdirname, outdirname, doctreedir,
                           status_stream=status, warning_stream=warning,
                           events=events, config=config, freshenv=freshenv)
    events.emit('builder-created', builder)


def usage(argv, msg=None):
    if msg:
        print >>sys.stderr, msg
        print >>sys.stderr
    print >>sys.stderr, """\
usage: %s [options] sourcedir outdir [filenames...]"
options: -b <builder> -- builder to use (one of %s)
         -a        -- write all files; default is to only write new and changed files
         -E        -- don't use a saved environment, always read all files
         -d <path> -- path for the cached environment and doctree files
                      (default outdir/.doctrees)
         -D <setting=value> -- override a setting in sourcedir/conf.py
         -N        -- do not do colored output
         -q        -- no output on stdout, just warnings on stderr
         -P        -- run Pdb on exception
modi:
* without -a and without filenames, write new and changed files.
* with -a, write all files.
* with filenames, write these.""" % (argv[0], ', '.join(builders))


def main(argv):
    if not sys.stdout.isatty() or sys.platform == 'win32':
        # Windows' poor cmd box doesn't understand ANSI sequences
        nocolor()

    try:
        opts, args = getopt.getopt(argv[1:], 'ab:d:D:NEqP')
        srcdirname = path.abspath(args[0])
        if not path.isdir(srcdirname):
            print >>sys.stderr, 'Error: Cannot find source directory.'
            return 1
        if not path.isfile(path.join(srcdirname, 'conf.py')):
            print >>sys.stderr, 'Error: Source directory doesn\'t contain conf.py file.'
            return 1
        outdirname = path.abspath(args[1])
        if not path.isdir(outdirname):
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
    doctreedir = path.join(outdirname, '.doctrees')
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

    builder = init_builder(buildername, srcdirname, outdirname, doctreedir,
                           confoverrides, status, sys.stderr, freshenv)
    if not builder:
        return 1

    try:
        if all_files:
            builder.build_all()
        elif filenames:
            builder.build_specific(filenames)
        else:
            builder.build_update()
    except:
        if not use_pdb:
            raise
        import pdb, traceback
        traceback.print_exc()
        pdb.post_mortem(sys.exc_info()[2])


if __name__ == '__main__':
    sys.exit(main(sys.argv))
