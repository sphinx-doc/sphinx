# -*- coding: utf-8 -*-
"""
    pytest config for sphinx/tests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

import pytest
from sphinx.testing.path import path

pytest_plugins = 'sphinx.testing.fixtures'


@pytest.fixture(scope='session')
def rootdir():
    return path(os.path.dirname(__file__) or '.').abspath() / 'roots'
