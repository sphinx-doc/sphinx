"""
    sphinx.environment.collectors.indexentries
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Index entries collector for sphinx.environment.

    :copyright: Copyright 2007-2021 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import Any, Dict, Set

from docutils import nodes

from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.environment import BuildEnvironment
from sphinx.environment.collectors import EnvironmentCollector
from sphinx.util import logging, split_index_msg

logger = logging.getLogger(__name__)


class IndexEntriesCollector(EnvironmentCollector):
    name = 'indices'

    def __init__(self) -> None:
        warnings.warn('IndexEntriesCollector is deprecated.',
                      RemovedInSphinx40Warning, stacklevel=2)

    def clear_doc(self, app: Sphinx, env: BuildEnvironment, docname: str) -> None:
        env.indexentries.pop(docname, None)

    def merge_other(self, app: Sphinx, env: BuildEnvironment,
                    docnames: Set[str], other: BuildEnvironment) -> None:
        for docname in docnames:
            env.indexentries[docname] = other.indexentries[docname]

    def process_doc(self, app: Sphinx, doctree: nodes.document) -> None:
        docname = app.env.docname
        entries = app.env.indexentries[docname] = []
        for node in doctree.traverse(addnodes.index):
            try:
                for entry in node['entries']:
                    split_index_msg(entry[0], entry[1])
            except ValueError as exc:
                logger.warning(str(exc), location=node)
                node.parent.remove(node)
            else:
                for entry in node['entries']:
                    entries.append(entry)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.add_env_collector(IndexEntriesCollector)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
