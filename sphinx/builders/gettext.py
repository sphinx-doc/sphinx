# -*- coding: utf-8 -*-
"""
    sphinx.builders.gettext
    ~~~~~~~~~~~~~~~~~~~~~~~

    The MessageCatalogBuilder class.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from os import path
from codecs import open
from datetime import datetime
from collections import defaultdict

from docutils import nodes

from sphinx.builders import Builder
from sphinx.util.nodes import extract_messages
from sphinx.util.osutil import SEP, copyfile
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
"POT-Creation-Date: %(ctime)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

"""[1:]


class I18nBuilder(Builder):
    """
    General i18n builder.
    """
    name = 'i18n'
    versioning_method = 'text'

    def init(self):
        Builder.init(self)
        self.catalogs = defaultdict(dict)

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        catalog = self.catalogs[docname.split(SEP, 1)[0]]

        for node, msg in extract_messages(doctree):
            catalog.setdefault(node.uid, msg)


class MessageCatalogBuilder(I18nBuilder):
    """
    Builds gettext-style message catalogs (.pot files).
    """
    name = 'gettext'

    def finish(self):
        I18nBuilder.finish(self)
        data = dict(
            version = self.config.version,
            copyright = self.config.copyright,
            project = self.config.project,
            # XXX should supply tz
            ctime = datetime.now().strftime('%Y-%m-%d %H:%M%z'),
        )
        for section, messages in self.status_iterator(
                self.catalogs.iteritems(), "writing message catalogs... ",
                lambda (section, _):darkgreen(section), len(self.catalogs)):

            pofn = path.join(self.outdir, section + '.pot')
            pofile = open(pofn, 'w', encoding='utf-8')
            try:
                pofile.write(POHEADER % data)
                for uid, message in messages.iteritems():
                    # message contains *one* line of text ready for translation
                    message = message.replace(u'\\', ur'\\'). \
                                      replace(u'"', ur'\"')
                    pomsg = u'#%s\nmsgid "%s"\nmsgstr ""\n\n' % (uid, message)
                    pofile.write(pomsg)
            finally:
                pofile.close()
