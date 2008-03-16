# -*- coding: utf-8 -*-
"""
    Sphinx - Python documentation webserver
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2008 by Armin Ronacher, Georg Brandl.
    :license: BSD.
"""

import sys

if __name__ == '__main__':
    print 'sphinx.web currently doesn\'t work -- it will undergo a ' \
          'serious rewrite soon.'
    sys.exit()
    from sphinx.web import main
    sys.exit(main(sys.argv))
