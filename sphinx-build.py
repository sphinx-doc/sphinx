#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx - Python documentation toolchain
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

if __name__ == '__main__':
    from sphinx import main, make_main
    if sys.argv[1:2] == ['-M']:
        sys.exit(make_main(sys.argv))
    else:
        sys.exit(main(sys.argv))
