#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx unit test driver
    ~~~~~~~~~~~~~~~~~~~~~~~

    This script runs the Sphinx unit test suite.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

import sys
from os import path

# always test the sphinx package from this directory
sys.path.insert(0, path.join(path.dirname(__file__), path.pardir))

try:
    import nose
except ImportError:
    print "The nose package is needed to run the Sphinx test suite."
    sys.exit(1)

print "Running Sphinx test suite..."
nose.main()
