#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx - Python documentation toolchain
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: 2007-2010 by Georg Brandl.
    :license: BSD.
"""

import sys

if __name__ == '__main__':
    from sphinx.ext.autosummary.generate import main
    sys.exit(main(sys.argv))
