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

import pytest  # NOQA
sys.exit(pytest.main(sys.argv[1:]))
