# -*- coding: utf-8 -*-
"""
    Sphinx
    ~~~~~~

    The Sphinx documentation toolchain.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import sys

__revision__ = '$Revision$'
__version__ = '0.5.1'
__released__ = '0.5.1'


def main(argv=sys.argv):
    if sys.version_info[:3] < (2, 4, 0):
        print >>sys.stderr, \
              'Error: Sphinx requires at least Python 2.4 to run.'
        return 1

    try:
        from sphinx import cmdline
    except ImportError, err:
        errstr = str(err)
        if errstr.lower().startswith('no module named'):
            whichmod = errstr[16:]
            if whichmod.startswith('docutils'):
                whichmod = 'Docutils library'
            elif whichmod.startswith('jinja'):
                whichmod = 'Jinja library'
            elif whichmod == 'roman':
                whichmod = 'roman module (which is distributed with Docutils)'
            else:
                whichmod += ' module'
            print >>sys.stderr, \
                  'Error: The %s cannot be found. Did you install Sphinx '\
                  'and its dependencies correctly?' % whichmod
            return 1
        raise
    return cmdline.main(argv)


if __name__ == '__main__':
    sys.exit(main(sys.argv))
