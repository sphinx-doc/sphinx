# -*- coding: utf-8 -*-
"""
    sphinx.environment.managers.indexentries
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Index entries manager for sphinx.environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx import addnodes
from sphinx.util import split_index_msg, logging
from sphinx.environment.managers import EnvironmentManager

if False:
    # For type annotation
    from docutils import nodes  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


class IndexEntries(EnvironmentManager):
    name = 'indices'

    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        super(IndexEntries, self).__init__(env)
        self.data = env.indexentries

    def clear_doc(self, docname):
        # type: (unicode) -> None
        self.data.pop(docname, None)

    def merge_other(self, docnames, other):
        # type: (List[unicode], BuildEnvironment) -> None
        for docname in docnames:
            self.data[docname] = other.indexentries[docname]

    def process_doc(self, docname, doctree):
        # type: (unicode, nodes.Node) -> None
        entries = self.data[docname] = []
        for node in doctree.traverse(addnodes.index):
            try:
                for entry in node['entries']:
                    split_index_msg(entry[0], entry[1])
            except ValueError as exc:
                logger.warning(str(exc), location=node)
                node.parent.remove(node)
            else:
                for entry in node['entries']:
                    if len(entry) == 5:
                        # Since 1.4: new index structure including index_key (5th column)
                        entries.append(entry)
                    else:
                        entries.append(entry + (None,))

    def get_updated_docs(self):
        # type: () -> List[unicode]
        return []
