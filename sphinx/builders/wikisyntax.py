# -*- coding: utf-8 -*-
"""
    sphinx.builders.wikisyntax
    ~~~~~~~~~~~~~~~~~~~~

    Wikisyntax Sphinx builder.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.builders.text import TextBuilder
from sphinx.writers.wikisyntax import WikisyntaxWriter


class WikisyntaxBuilder(TextBuilder):
    name = 'wikisyntax'
    format = 'wikisyntax'
    out_suffix = '.wiki'
    allow_parallel = True

    def prepare_writing(self, docnames):
        self.writer = WikisyntaxWriter(self)
