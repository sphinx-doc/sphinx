# -*- coding: utf-8 -*-
"""
    sphinx._jinja
    ~~~~~~~~~~~~~

    Jinja glue.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""
from __future__ import absolute_import

import sys
from os import path

sys.path.insert(0, path.dirname(__file__))

from jinja import Environment, FileSystemLoader
