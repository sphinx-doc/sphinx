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
        # The translator needs the docname to generate ids.
        self.docname = docname
        PickleHTMLBuilder.write_doc(self, docname, doctree)

    def handle_page(self, pagename, ctx, templatename='', **ignored):
        # Mostly copied from PickleHTMLBuilder.
        ctx['current_page_name'] = ctx['pagename'] = pagename
        self.add_sidebars(pagename, ctx)

        self.app.emit('html-page-context', pagename, ctx)

        # Instead of pickling ctx as PickleHTMLBuilder does, we
        # have created a Document object and pickle that.
        document = self.docwriter.visitor.support_document
        document.__dict__.update(ctx)

        doc_filename = path.join(self.outdir,
                                 os_path(pagename) + self.out_suffix)
        ensuredir(path.dirname(doc_filename))
        f = open(doc_filename, 'wb')
        try:
            self.implementation.dump(document, f)
        finally:
            f.close()

    def get_target_uri(self, docname, typ=None):
        return docname
