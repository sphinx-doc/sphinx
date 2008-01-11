# -*- coding: utf-8 -*-
"""
    Convert the Python documentation to Sphinx
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import sys
import os

from converter import convert_dir

if __name__ == '__main__':
    try:
        rootdir = sys.argv[1]
        destdir = os.path.abspath(sys.argv[2])
    except IndexError:
        print "usage: convert.py docrootdir destdir"
        sys.exit()

    assert os.path.isdir(os.path.join(rootdir, 'texinputs'))
    os.chdir(rootdir)
    convert_dir(destdir, *sys.argv[3:])
