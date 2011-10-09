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

from sphinx.builders import Builder
from sphinx.util.nodes import extract_messages
from sphinx.util.osutil import SEP, safe_relpath, ensuredir, find_catalog
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
"Project-Id-Version: %(project)s %(version)s\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: %(ctime)s\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"

"""[1:]


class Catalog(object):
    """Catalog of translatable messages."""

    def __init__(self):
        self.messages = []  # retain insertion order, a la OrderedDict
        self.metadata = {}  # msgid -> file, line, uid

    def add(self, msg, origin):
        if msg not in self.metadata:  # faster lookup in hash
            self.messages.append(msg)
            self.metadata[msg] = []
        self.metadata[msg].append((origin.source, origin.line, origin.uid))


class I18nBuilder(Builder):
    """
    General i18n builder.
    """
    name = 'i18n'
    versioning_method = 'text'

    def init(self):
        Builder.init(self)
        self.catalogs = defaultdict(Catalog)

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        catalog = self.catalogs[find_catalog(docname,
                                             self.config.gettext_compact)]

        for node, msg in extract_messages(doctree):
            catalog.add(msg, node)


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
        for textdomain, catalog in self.status_iterator(
                self.catalogs.iteritems(), "writing message catalogs... ",
                lambda (textdomain, _): darkgreen(textdomain),
                                        len(self.catalogs)):

            # noop if config.gettext_compact is set
            ensuredir(path.join(self.outdir, path.dirname(textdomain)))

            pofn = path.join(self.outdir, textdomain + '.pot')
            pofile = open(pofn, 'w', encoding='utf-8')
            try:
                pofile.write(POHEADER % data)

                for message in catalog.messages:
                    positions = catalog.metadata[message]

                    # generate "#: file1:line1\n#: file2:line2 ..."
                    pofile.write(u"#: %s\n" % "\n#: ".join("%s:%s" %
                        (safe_relpath(source, self.outdir), line)
                        for source, line, _ in positions))
                    # generate "# uuid1\n# uuid2\n ..."
                    pofile.write(u"# %s\n" % "\n# ".join(uid for _, _, uid
                        in positions))

                    # message contains *one* line of text ready for translation
                    message = message.replace(u'\\', ur'\\'). \
                                      replace(u'"', ur'\"')
                    pofile.write(u'msgid "%s"\nmsgstr ""\n\n' % message)

            finally:
                pofile.close()
