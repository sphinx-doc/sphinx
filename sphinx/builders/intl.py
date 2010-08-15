# -*- coding: utf-8 -*-
"""
    sphinx.builders.intl
    ~~~~~~~~~~~~~~~~~~~~

    The MessageCatalogBuilder class.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import defaultdict
from datetime import datetime
from os import path
from codecs import open
import os
import pickle

from docutils import nodes
from docutils.utils import Reporter

from sphinx.builders import Builder
from sphinx.util.nodes import extract_messages
from sphinx.util.osutil import SEP, copyfile
from sphinx.util.console import darkgreen
from sphinx.environment import WarningStream
from sphinx.versioning import add_uids, merge_doctrees

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

class I18NBuilder(Builder):
    name = 'i18n'

    def init(self):
        Builder.init(self)
        self.catalogs = defaultdict(dict)
        for root, dirs, files in os.walk(self.doctreedir):
            for fn in files:
                fp = path.join(root, fn)
                if fp.endswith('.doctree'):
                    copyfile(fp, fp + '.old')

    def get_old_doctree(self, docname):
        fp = self.env.doc2path(docname, self.doctreedir, '.doctree.old')
        try:
            f = open(fp, 'rb')
            try:
                doctree = pickle.load(f)
            finally:
                f.close()
        except IOError:
            return None
        doctree.settings.env = self.env
        doctree.reporter = Reporter(self.env.doc2path(docname), 2, 5,
                                    stream=WarningStream(self.env._warnfunc))

    def resave_doctree(self, docname, doctree):
        reporter = doctree.reporter
        doctree.reporter = None
        doctree.settings.warning_stream = None
        doctree.settings.env = None
        doctree.settings.record_dependencies = None

        fp = self.env.doc2path(docname, self.doctreedir, '.doctree')
        f = open(fp, 'wb')
        try:
            pickle.dump(doctree, f, pickle.HIGHEST_PROTOCOL)
        finally:
            f.close()

        doctree.reporter = reporter

    def get_target_uri(self, docname, typ=None):
        return ''

    def get_outdated_docs(self):
        return self.env.found_docs

    def prepare_writing(self, docnames):
        return

    def write_doc(self, docname, doctree):
        catalog = self.catalogs[docname.split(SEP, 1)[0]]
        old_doctree = self.get_old_doctree(docname)

        if old_doctree:
            list(merge_doctrees(old_doctree, doctree, nodes.TextElement))
        else:
            list(add_uids(doctree, nodes.TextElement))
        self.resave_doctree(docname, doctree)

        for node, msg in extract_messages(doctree):
            catalog.setdefault(node.uid, msg)

    def finish(self):
        Builder.finish(self)
        for root, dirs, files in os.walk(self.doctreedir):
            for fn in files:
                fp = path.join(root, fn)
                if fp.endswith('.doctree.old'):
                    os.remove(fp)

class MessageCatalogBuilder(I18NBuilder):
    """
    Builds gettext-style message catalogs (.pot files).
    """
    name = 'gettext'

    def finish(self):
        I18NBuilder.finish(self)
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

            pofp = path.join(self.outdir, section + '.pot')
            pofile = open(pofp, 'w', encoding='utf-8')
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
