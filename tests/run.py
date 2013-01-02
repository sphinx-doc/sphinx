#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx unit test driver
    ~~~~~~~~~~~~~~~~~~~~~~~

    This script runs the Sphinx unit test suite.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from os import path, chdir, listdir, environ

if sys.version_info >= (3, 0):
    print('Copying and converting sources to build/lib/tests...')
    from distutils.util import copydir_run_2to3
    testroot = path.dirname(__file__) or '.'
    if 'BUILD_TEST_PATH' in environ:
        # for tox testing
        newroot = environ['BUILD_TEST_PATH']
        # tox installs the sphinx package, no need for sys.path.insert
    else:
        newroot = path.join(testroot, path.pardir, 'build')
        newroot = path.join(newroot, listdir(newroot)[0], 'tests')
        # always test the sphinx package from build/lib/
        sys.path.insert(0, path.abspath(path.join(newroot, path.pardir)))
    copydir_run_2to3(testroot, newroot)
    # switch to the converted dir so nose tests the right tests
    chdir(newroot)
else:
    # always test the sphinx package from this directory
    sys.path.insert(0, path.join(path.dirname(__file__), path.pardir))

try:
    import nose
except ImportError:
    print('The nose package is needed to run the Sphinx test suite.')
    sys.exit(1)

try:
    import docutils
except ImportError:
    print('Sphinx requires the docutils package to be installed.')
    sys.exit(1)

try:
    import jinja2
except ImportError:
    print('Sphinx requires the jinja2 package to be installed.')
    sys.exit(1)

print('Running Sphinx test suite...')
nose.main()
