#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Sphinx unit test driver
    ~~~~~~~~~~~~~~~~~~~~~~~

    This script runs the Sphinx unit test suite.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import sys

import pytest

sys.exit(pytest.main(sys.argv[1:]))
