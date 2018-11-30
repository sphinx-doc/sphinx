# -*- coding: utf-8 -*-
"""
    pytest config for sphinx/tests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import shutil

import docutils
import pytest

import sphinx
from sphinx.testing.path import path

pytest_plugins = 'sphinx.testing.fixtures'

# Exclude 'roots' dirs for pytest test collector
collect_ignore = ['roots']


@pytest.fixture(scope='session')
def rootdir():
    return path(os.path.dirname(__file__)).abspath() / 'roots'


def pytest_report_header(config):
    return ("libraries: Sphinx-%s, docutils-%s" %
            (sphinx.__display_version__, docutils.__version__))


def _initialize_test_directory(session):
    testroot = os.path.join(str(session.config.rootdir), 'tests')
    tempdir = os.path.abspath(os.getenv('SPHINX_TEST_TEMPDIR',
                              os.path.join(testroot, 'build')))
    os.environ['SPHINX_TEST_TEMPDIR'] = tempdir

    print('Temporary files will be placed in %s.' % tempdir)

    if os.path.exists(tempdir):
        shutil.rmtree(tempdir)

    os.makedirs(tempdir)


def pytest_sessionstart(session):
    _initialize_test_directory(session)
