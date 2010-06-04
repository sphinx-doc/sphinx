# -*- coding: utf-8 -*-
"""
    sphinx.websupport.api
    ~~~~~~~~~~~~~~~~~~~~

    All API functions.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import cPickle as pickle
from os import path

from sphinx.application import Sphinx

class WebSupport(object):
    
    def init(self, srcdir='', outdir=''):
        self.srcdir = srcdir
        self.outdir = outdir or path.join(self.srcdir, '_build',
                                          'websupport')

    def build(self, **kwargs):
        doctreedir = kwargs.pop('doctreedir', 
                                path.join(self.outdir, 'doctrees'))
        app = Sphinx(self.srcdir, self.srcdir,
                     self.outdir, doctreedir, 'websupport')
        app.build()

    def get_document(self, docname):
        infilename = path.join(self.outdir, docname + '.fpickle')
        f = open(infilename, 'rb')
        document = pickle.load(f)
        return document
