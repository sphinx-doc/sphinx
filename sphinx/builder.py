# -*- coding: utf-8 -*-
"""
    sphinx.builder
    ~~~~~~~~~~~~~~

    .. warning::

       This module is only kept for API compatibility; new code should
       import these classes directly from the sphinx.builders package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from sphinx.builders import Builder
from sphinx.builders.text import TextBuilder
from sphinx.builders.html import StandaloneHTMLBuilder, WebHTMLBuilder, \
     PickleHTMLBuilder, JSONHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder
from sphinx.builders.changes import ChangesBuilder
from sphinx.builders.htmlhelp import HTMLHelpBuilder
from sphinx.builders.linkcheck import CheckExternalLinksBuilder

warnings.warn('The sphinx.builder module is deprecated; please import '
              'builders from the respective sphinx.builders submodules.',
              DeprecationWarning, stacklevel=2)
