# -*- coding: utf-8 -*-
"""
    sphinx.builders.websupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Builder for the web support package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path

from sphinx.util.osutil import ensuredir, os_path
from sphinx.builders.html import PickleHTMLBuilder
from sphinx.writers.websupport import WebSupportTranslator

class WebSupportBuilder(PickleHTMLBuilder):
    """
    Builds documents for the web support package.
    """
    name = 'websupport'
    template_suffix = '.html'
    
    def init_translator_class(self):
        self.translator_class = WebSupportTranslator
        
    def write_doc(self, docname, doctree):
        # The translator needs the docuname to generate ids.
        self.docname = docname
        PickleHTMLBuilder.write_doc(self, docname, doctree)

    def handle_page(self, pagename, ctx, templatename='', **ignored):
        # Mostly copied from PickleHTMLBuilder.
        ctx['current_page_name'] = pagename
        self.add_sidebars(pagename, ctx)

        self.app.emit('html-page-context', pagename, ctx)

        # Instead of pickling ctx as PickleHTMLBuilder does, we
        # create a Document object and pickle that.
        document = self.docwriter.visitor.support_document
        document.body = ctx['body'] if 'body' in ctx else ''
        document.title = ctx['title'] if 'title' in ctx else ''

        doc_filename = path.join(self.outdir,
                                 os_path(pagename) + self.out_suffix)
        ensuredir(path.dirname(doc_filename))
        f = open(doc_filename, 'wb')
        try:
            self.implementation.dump(document, f, 2)
        finally:
            f.close()

    def get_target_uri(self, docname, typ=None):
        return docname
