"""
    pytest config for sphinx/tests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

import docutils
import pytest

import sphinx
from sphinx.testing.path import path
from sphinx.testing import comparer

pytest_plugins = 'sphinx.testing.fixtures'

# Exclude 'roots' dirs for pytest test collector
collect_ignore = ['roots']


@pytest.fixture(scope='session')
def rootdir():
    return path(os.path.dirname(__file__)).abspath() / 'roots'


def pytest_report_header(config):
    return ("libraries: Sphinx-%s, docutils-%s" %
            (sphinx.__display_version__, docutils.__version__))


def pytest_assertrepr_compare(op, left, right):
    comparer.pytest_assertrepr_compare(op, left, right)
