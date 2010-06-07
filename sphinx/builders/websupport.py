# -*- coding: utf-8 -*-
"""
    sphinx.builders.websupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Builder for the web support package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.builders.html import PickleHTMLBuilder
from sphinx.writers.websupport import WebSupportTranslator

class WebSupportBuilder(PickleHTMLBuilder):
    """
    Builds documents for the web support package.
    """
    name = 'websupport'
    
    def init_translator_class(self):
        self.translator_class = WebSupportTranslator
        
    def write_doc(self, docname, doctree):
        # The translator needs the docname to generate ids.
        self.docname = docname
        PickleHTMLBuilder.write_doc(self, docname, doctree)

    def get_target_uri(self, docname, typ=None):
        return docname
