# -*- coding: utf-8 -*-
"""
    sphinx.builders.intl
    ~~~~~~~~~~~~~~~~~~~~

    The MessageCatalogBuilder class.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import collections
from os import path

from docutils import nodes

from sphinx.builders import Builder
from sphinx.util.nodes import extract_messages
from sphinx.util.console import darkgreen

POHEADER = ur"""
# SOME DESCRIPTIVE TITLE.
# Copyright (C) %(copyright)s
# This file is distributed under the same license as the %(project)s package.
# FIRST AUTHOR <EMAIL@ADDRESS>, YEAR.
#
#, fuzzy
msgid ""
msgstr ""
"Project-Id-Version: %(version)s\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: %(gettext_ctime)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

"""[1:]

class MessageCatalogBuilder(Builder):
    """
    Builds gettext-style message catalogs (.pot files).
    """
    name = 'gettext'

    def init(self):
        self.catalogs = collections.defaultdict(list)

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        """
        Store a document's translatable strings in the message catalog of its
        section. For this purpose a document's *top-level directory* -- or
        otherwise its *name* -- is considered its section.
        """
        catalog = self.catalogs[docname.split('/')[0]]
        for msg in extract_messages(doctree):
            # XXX msgctxt for duplicate messages
            if msg not in catalog:
                catalog.append(msg)

    def finish(self):
        for section, messages in self.status_iterator(
                self.catalogs.iteritems(), "writing message catalogs... ",
                lambda (section, _):darkgreen(section), len(self.catalogs)):
            pofile = open(path.join(self.outdir, '%s.pot' % section), 'w')
            try:
                pofile.write(POHEADER % self.config)
                for message in messages:
                    # message contains *one* line of text ready for translation
                    message = message.replace(u'\\', ur'\\').replace(u'"', ur'\"')
                    pomsg = u'msgid "%s"\nmsgstr ""\n\n' % message
                    pofile.write(pomsg.encode('utf-8'))
            finally:
                pofile.close()
