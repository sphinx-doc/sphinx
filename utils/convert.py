#!/usr/bin/env python3
# coding: utf-8
"""
    Converts files with 2to3
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Creates a Python 3 version of each file.

    The Python3 version of a file foo.py will be called foo3.py.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import sys
from glob import iglob
from optparse import OptionParser
from shutil import copy
from distutils.util import run_2to3

def main(argv):
    parser = OptionParser(usage='%prog [path]')
    parser.add_option('-i', '--ignorepath', dest='ignored_paths',
                      action='append', default=[])
    options, args = parser.parse_args(argv)

    ignored_paths = {os.path.abspath(p) for p in options.ignored_paths}

    path = os.path.abspath(args[0]) if args else os.getcwd()
    convertables = []
    for filename in iglob(os.path.join(path, '*.py')):
        if filename in ignored_paths:
            continue
        basename, ext = os.path.splitext(filename)
        if basename.endswith('3'):
            continue
        filename3 = basename + '3' + ext
        copy(filename, filename3)
        convertables.append(filename3)
    run_2to3(convertables)

if __name__ == "__main__":
    main(sys.argv[1:])
