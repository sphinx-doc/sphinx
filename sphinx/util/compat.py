# -*- coding: utf-8 -*-
"""
    sphinx.util.compat
    ~~~~~~~~~~~~~~~~~~

    Stuff for docutils compatibility.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

import sys
import warnings
from distutils.version import LooseVersion

from docutils.parsers.rst import Directive  # noqa
from docutils import __version__ as _du_version

from sphinx.deprecation import RemovedInSphinx17Warning

docutils_version = tuple(LooseVersion(_du_version).version)[:2]

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA


class _DeprecationWrapper(object):
    def __init__(self, mod, deprecated):
        # type: (Any, Dict) -> None
        self._mod = mod
        self._deprecated = deprecated

    def __getattr__(self, attr):
        # type: (str) -> Any
        if attr in self._deprecated:
            warnings.warn("sphinx.util.compat.%s is deprecated and will be removed "
                          "in Sphinx 1.7, please use docutils' instead." % attr,
                          RemovedInSphinx17Warning)
            return self._deprecated[attr]
        return getattr(self._mod, attr)


sys.modules[__name__] = _DeprecationWrapper(sys.modules[__name__], dict(  # type: ignore
    docutils_version = docutils_version,
    Directive = Directive,
))
