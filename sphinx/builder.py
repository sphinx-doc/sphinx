# -*- coding: utf-8 -*-
"""
    sphinx.builder
    ~~~~~~~~~~~~~~

    .. warning::

       This module is only kept for API compatibility; new code should
       import these classes directly from the sphinx.builders package.

    :copyright: 2008 by Georg Brandl.
    :license: BSD.
"""

from sphinx.builders import Builder
from sphinx.builders.text import TextBuilder
from sphinx.builders.html import StandaloneHTMLBuilder, WebHTMLBuilder, \
     PickleHTMLBuilder, JSONHTMLBuilder
from sphinx.builders.latex import LaTeXBuilder
from sphinx.builders.changes import ChangesBuilder
from sphinx.builders.htmlhelp import HTMLHelpBuilder
from sphinx.builders.linkcheck import CheckExternalLinksBuilder
