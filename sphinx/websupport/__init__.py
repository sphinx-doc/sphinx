# -*- coding: utf-8 -*-
"""
    sphinx.websupport
    ~~~~~~~~~~~~~~~~~

    Base Module for web support functions.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from sphinx.deprecation import RemovedInSphinx20Warning
from sphinxcontrib.websupport import WebSupport  # NOQA
from sphinxcontrib.websupport import errors  # NOQA
from sphinxcontrib.websupport.search import BaseSearch, SEARCH_ADAPTERS  # NOQA
from sphinxcontrib.websupport.storage import StorageBackend  # NOQA

warnings.warn('sphinx.websupport module is now provided as sphinxcontrib.webuspport. '
              'sphinx.websupport will be removed in Sphinx-2.0.  Please use it instaed',
              RemovedInSphinx20Warning)
