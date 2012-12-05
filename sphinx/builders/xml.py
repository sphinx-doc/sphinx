# -*- coding: utf-8 -*-
"""
    sphinx.builders.xml
    ~~~~~~~~~~~~~~~~~~~

    Docutils-native XML and pseudo-XML builders.

    :copyright: Copyright 2007-2012 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import codecs
from os import path

from docutils.io import StringOutput

from sphinx.builders import Builder
from sphinx.util.osutil import ensuredir, os_path
from sphinx.writers.xml import XMLWriter, PseudoXMLWriter

class XMLBuilder(Builder):
    """
    Builds Docutils-native XML.
    """
    name = 'xml'
    format = 'xml'
    out_suffix = '.xml'

    _writer_class = XMLWriter

    def init(self):
        pass

    def get_outdated_docs(self):
        for docname in self.env.found_docs:
            if docname not in self.env.all_docs:
                yield docname
                continue
            targetname = self.env.doc2path(docname, self.outdir,
                                           self.out_suffix)
            try:
                targetmtime = path.getmtime(targetname)
            except Exception:
                targetmtime = 0
            try:
                srcmtime = path.getmtime(self.env.doc2path(docname))
                if srcmtime > targetmtime:
                    yield docname
            except EnvironmentError:
                # source doesn't exist anymore
                pass

    def get_target_uri(self, docname, typ=None):
        return ''

    def prepare_writing(self, docnames):
        self.writer = self._writer_class(self)

    def write_doc(self, docname, doctree):
        destination = StringOutput(encoding='utf-8')
        self.writer.write(doctree, destination)
        outfilename = path.join(self.outdir, os_path(docname) + self.out_suffix)
        ensuredir(path.dirname(outfilename))
        try:
            f = codecs.open(outfilename, 'w', 'utf-8')
            try:
                f.write(self.writer.output)
            finally:
                f.close()
        except (IOError, OSError), err:
            self.warn("error writing file %s: %s" % (outfilename, err))

    def finish(self):
        pass


class PseudoXMLBuilder(XMLBuilder):
    """
    Builds pseudo-XML for display purposes.
    """
    name = 'pseudoxml'
    format = 'pseudoxml'
    out_suffix = '.pseudoxml'

    _writer_class = PseudoXMLWriter
