#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx - Python documentation toolchain
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

if __name__ == '__main__':
    from sphinx.ext.autosummary.generate import main
    sys.exit(main(sys.argv))
