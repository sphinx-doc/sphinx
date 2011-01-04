# -*- coding: utf-8 -*-
"""
    sphinx.builders.versioning
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import cPickle as pickle

from docutils.utils import Reporter

from sphinx.util.osutil import copyfile
from sphinx.environment import WarningStream
from sphinx.versioning import add_uids, merge_doctrees


class VersioningBuilderMixin(object):
    def walk_doctree_files(self):
        for root, dirs, files in os.walk(self.doctreedir):
            for fn in files:
                yield os.path.join(root, fn)

    def init(self):
        for fp in self.walk_doctree_files():
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
        return doctree

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

    def handle_versioning(self, docname, doctree, condition):
        old_doctree = self.get_old_doctree(docname)
        if old_doctree:
            list(merge_doctrees(old_doctree, doctree, condition))
        else:
            list(add_uids(doctree, condition))
        self.resave_doctree(docname, doctree)

    def finish(self):
        for fp in self.walk_doctree_files():
            if fp.endswith('.doctree.old'):
                os.remove(fp)
