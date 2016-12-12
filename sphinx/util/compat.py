# -*- coding: utf-8 -*-
"""
    sphinx.util.compat
    ~~~~~~~~~~~~~~~~~~

    Stuff for docutils compatibility.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

from docutils.parsers.rst import Directive  # noqa

from docutils import __version__ as _du_version
docutils_version = tuple(int(x) for x in _du_version.split('.')[:2])
