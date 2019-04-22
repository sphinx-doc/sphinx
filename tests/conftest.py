"""
    pytest config for sphinx/tests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import shutil

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
    return path(__file__).parent.abspath() / 'roots'


def pytest_report_header(config):
    header = ("libraries: Sphinx-%s, docutils-%s" %
              (sphinx.__display_version__, docutils.__version__))
    if hasattr(config, '_tmp_path_factory'):
        header += "\nbase tempdir: %s" % config._tmp_path_factory.getbasetemp()

    return header


def pytest_assertrepr_compare(op, left, right):
    comparer.pytest_assertrepr_compare(op, left, right)


@pytest.fixture(scope="session", autouse=True)
def _initialize_test_directory(request):
    tempdir = getattr(request.config, "slaveinput", {}).get("slaveid")
    if 'SPHINX_TEST_TEMPDIR' in os.environ:
        prefix = os.path.abspath(os.getenv('SPHINX_TEST_TEMPDIR'))
        if tempdir:
            tempdir = '{0}_{1}'.format(prefix, tempdir)
        else:
            tempdir = prefix
    if tempdir:
        print('Temporary files will be placed in %s.' % tempdir)

        if os.path.exists(tempdir):
            shutil.rmtree(tempdir)

        os.makedirs(tempdir)
