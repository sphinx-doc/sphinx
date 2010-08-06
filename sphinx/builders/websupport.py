# -*- coding: utf-8 -*-
"""
    sphinx.builders.websupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Builder for the web support package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import cPickle as pickle
from os import path
import posixpath
import shutil
from docutils.io import StringOutput

from sphinx.util.osutil import os_path, relative_uri, ensuredir, copyfile
from sphinx.builders.html import StandaloneHTMLBuilder
from sphinx.writers.websupport import WebSupportTranslator

class WebSupportBuilder(StandaloneHTMLBuilder):
    """
    Builds documents for the web support package.
    """
    name = 'websupport'
    out_suffix = '.fpickle'

    def init_translator_class(self):
        self.translator_class = WebSupportTranslator

    def write_doc(self, docname, doctree):
        # The translator needs the docname to generate ids.
        self.cur_docname = docname
        destination = StringOutput(encoding='utf-8')
        doctree.settings = self.docsettings

        self.secnumbers = self.env.toc_secnumbers.get(docname, {})
        self.imgpath = '/' + posixpath.join(self.app.staticdir, '_images')
        self.post_process_images(doctree)
        self.dlpath = '/' + posixpath.join(self.app.staticdir, '_downloads')
        self.docwriter.write(doctree, destination)
        self.docwriter.assemble_parts()
        body = self.docwriter.parts['fragment']
        metatags = self.docwriter.clean_meta

        ctx = self.get_doc_context(docname, body, metatags)
        self.index_page(docname, doctree, ctx.get('title', ''))
        self.handle_page(docname, ctx, event_arg=doctree)

    def get_target_uri(self, docname, typ=None):
        return docname

    def load_indexer(self, docnames):
        self.indexer = self.app.search
        self.indexer.init_indexing(changed=docnames)

    def handle_page(self, pagename, addctx, templatename='page.html',
                    outfilename=None, event_arg=None):
        # This is mostly copied from StandaloneHTMLBuilder. However, instead
        # of rendering the template and saving the html, create a context 
        # dict and pickle it.
        ctx = self.globalcontext.copy()
        ctx['pagename'] = pagename

        def pathto(otheruri, resource=False,
                   baseuri=self.get_target_uri(pagename)):
            if not resource:
                otheruri = self.get_target_uri(otheruri)
                return relative_uri(baseuri, otheruri) or '#'
            else:
                return '/' + posixpath.join(self.app.staticdir, otheruri)
        ctx['pathto'] = pathto
        ctx['hasdoc'] = lambda name: name in self.env.all_docs
        ctx['encoding'] = encoding = self.config.html_output_encoding
        ctx['toctree'] = lambda **kw: self._get_local_toctree(pagename, **kw)
        self.add_sidebars(pagename, ctx)
        ctx.update(addctx)

        self.app.emit('html-page-context', pagename, templatename,
                      ctx, event_arg)

        # Create a dict that will be pickled and used by webapps.
        doc_ctx = {'body': ctx.get('body', ''),
                   'title': ctx.get('title', '')}
        # Partially render the html template to proved a more useful ctx.
        template = self.templates.environment.get_template(templatename)
        template_module = template.make_module(ctx)
        if hasattr(template_module, 'sidebar'):
            doc_ctx['sidebar'] = template_module.sidebar()
        if hasattr(template_module, 'relbar'):
            doc_ctx['relbar'] = template_module.relbar()

        if not outfilename:
            outfilename = path.join(self.outdir, 'pickles',
                                    os_path(pagename) + self.out_suffix)

        ensuredir(path.dirname(outfilename))
        f = open(outfilename, 'wb')
        try:
            pickle.dump(doc_ctx, f, 2)
        finally:
            f.close()

        # if there is a source file, copy the source file for the
        # "show source" link
        if ctx.get('sourcename'):
            source_name = path.join(self.outdir, self.app.staticdir,
                                    '_sources',  os_path(ctx['sourcename']))
            ensuredir(path.dirname(source_name))
            copyfile(self.env.doc2path(pagename), source_name)

    def handle_finish(self):
        StandaloneHTMLBuilder.handle_finish(self)
        shutil.move(path.join(self.outdir, '_images'),
                    path.join(self.outdir, self.app.staticdir, '_images'))
        shutil.move(path.join(self.outdir, '_static'),
                    path.join(self.outdir, self.app.staticdir, '_static'))

    def dump_search_index(self):
        self.indexer.finish_indexing()
