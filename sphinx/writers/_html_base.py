"""docutils writers handling Sphinx' custom nodes."""

import os
import posixpath
import re
import urllib.parse
import warnings
from typing import TYPE_CHECKING, Iterable, Optional, Tuple, cast

from docutils import nodes
from docutils.nodes import Element, Node, Text
from docutils.writers.html4css1 import HTMLTranslator as BaseTranslator
from docutils.writers.html4css1 import Writer

from sphinx import addnodes
from sphinx.builders import Builder
from sphinx.deprecation import RemovedInSphinx60Warning
from sphinx.locale import _, __, admonitionlabels
from sphinx.util import logging
from sphinx.util.docutils import SphinxTranslator
from sphinx.util.images import get_image_size

if TYPE_CHECKING:
    from sphinx.builders.html import StandaloneHTMLBuilder


logger = logging.getLogger(__name__)


class HTMLTranslatorBase(SphinxTranslator, BaseTranslator):
    """
    Our custom HTML translator base.

    This base class is specialised for HTML and HTML5.
    """

    builder: "StandaloneHTMLBuilder"

    def __init__(self, document: nodes.document, builder: "StandaloneHTMLBuilder") -> None:
        super().__init__(document, builder)

        self.highlighter = self.builder.highlighter
        self.docnames = [self.builder.current_docname]  # for singlehtml builder
        self.manpages_url = self.config.manpages_url
        self.protect_literal_text = 0
        self.secnumber_suffix = self.config.html_secnumber_suffix
        self.param_separator = ''
        self.optional_param_level = 0
        self._table_row_indices = [0]
        self._fieldlist_row_indices = [0]
        self.required_params_left = 0
