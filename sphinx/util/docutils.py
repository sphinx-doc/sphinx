# -*- coding: utf-8 -*-
"""
    sphinx.util.docutils
    ~~~~~~~~~~~~~~~~~~~~

    Utility functions for docutils.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

from copy import copy
from contextlib import contextmanager
from docutils.parsers.rst import directives, roles


@contextmanager
def docutils_namespace():
    """Create namespace for reST parsers."""
    try:
        _directives = copy(directives._directives)
        _roles = copy(roles._roles)

        yield
    finally:
        directives._directives = _directives
        roles._roles = _roles
