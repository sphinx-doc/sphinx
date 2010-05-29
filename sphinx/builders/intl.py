# -*- coding: utf-8 -*-
"""
    sphinx.builders.intl
    ~~~~~~~~~~~~~~~~~~~~

    The MessageCatalogBuilder class.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.builders import Builder

class MessageCatalogBuilder(Builder):
    pass

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        return

    def finish(self):
        return
