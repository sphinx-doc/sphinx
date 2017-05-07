#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx unit test driver
    ~~~~~~~~~~~~~~~~~~~~~~~

    This script runs the Sphinx unit test suite.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import sys
import warnings
import traceback
import shutil

testroot = os.path.dirname(__file__) or '.'
sys.path.insert(0, os.path.abspath(os.path.join(testroot, os.path.pardir)))

# filter warnings of test dependencies
warnings.filterwarnings('ignore', category=DeprecationWarning, module='site')  # virtualenv
warnings.filterwarnings('ignore', category=ImportWarning, module='backports')
warnings.filterwarnings('ignore', category=ImportWarning, module='pkgutil')
warnings.filterwarnings('ignore', category=ImportWarning, module='pytest_cov')
warnings.filterwarnings('ignore', category=PendingDeprecationWarning, module=r'_pytest\..*')

# check dependencies before testing
print('Checking dependencies...')
for modname in ('pytest', 'mock', 'six', 'docutils', 'jinja2', 'pygments',
                'snowballstemmer', 'babel', 'html5lib'):
    try:
        __import__(modname)
    except ImportError as err:
        if modname == 'mock' and sys.version_info[0] == 3:
            continue
        traceback.print_exc()
        print('The %r package is needed to run the Sphinx test suite.' % modname)
        sys.exit(1)

# find a temp dir for testing and clean it up now
os.environ['SPHINX_TEST_TEMPDIR'] = \
    os.path.abspath(os.path.join(testroot, 'build')) \
    if 'SPHINX_TEST_TEMPDIR' not in os.environ \
    else os.path.abspath(os.environ['SPHINX_TEST_TEMPDIR'])

tempdir = os.environ['SPHINX_TEST_TEMPDIR']
print('Temporary files will be placed in %s.' % tempdir)
if os.path.exists(tempdir):
    shutil.rmtree(tempdir)
os.makedirs(tempdir)

print('Running Sphinx test suite (with Python %s)...' % sys.version.split()[0])
sys.stdout.flush()

# exclude 'roots' dirs for pytest test collector
ignore_paths = [
    os.path.relpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), sub))
    for sub in ('roots',)
]
args = sys.argv[1:]
for ignore_path in ignore_paths:
    args.extend(['--ignore', ignore_path])

import pytest  # NOQA
sys.exit(pytest.main(args))
