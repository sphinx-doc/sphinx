# -*- coding: utf-8 -*-
"""
    pytest config for sphinx/tests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import sys

import pytest
from sphinx.testing.path import path

pytest_plugins = 'sphinx.testing.fixtures'

# Exclude 'roots' dirs for pytest test collector
collect_ignore = ['roots']

# Disable Python version-specific
if sys.version_info < (3, 5):
    collect_ignore += ['py35']


@pytest.fixture(scope='session')
def rootdir():
    return path(os.path.dirname(__file__) or '.').abspath() / 'roots'


def pytest_report_header(config):
    return 'Running Sphinx test suite (with Python %s)...' % (
        sys.version.split()[0])
