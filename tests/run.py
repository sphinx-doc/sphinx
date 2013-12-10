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
import shutil

testroot = path.dirname(__file__) or '.'
if 'BUILD_TEST_PATH' in environ:
    # for tox testing
    newroot = environ['BUILD_TEST_PATH']
    # tox installs the sphinx package, no need for sys.path.insert
else:
    newroot = path.join(testroot, path.pardir, 'build')
    newroot = path.join(newroot, listdir(newroot)[0], 'tests')

shutil.rmtree(newroot, ignore_errors=True)

if sys.version_info >= (3, 0):
    print('Copying and converting sources to build/lib/tests...')
    from distutils.util import copydir_run_2to3
    copydir_run_2to3(testroot, newroot)
else:
    # just copying test directory to parallel testing
    print('Copying sources to build/lib/tests...')
    shutil.copytree(testroot, newroot)

# always test the sphinx package from build/lib/
sys.path.insert(0, path.abspath(path.join(newroot, path.pardir)))
# switch to the copy/converted dir so nose tests the right tests
chdir(newroot)

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
