"""
    sphinx.domains.index
    ~~~~~~~~~~~~~~~~~~~~

    The index domain.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Any, Dict, Iterable, List, Tuple

from docutils.nodes import Node

from sphinx import addnodes
from sphinx.application import Sphinx
from sphinx.domains import Domain
from sphinx.environment import BuildEnvironment
from sphinx.util import logging
from sphinx.util import split_index_msg


logger = logging.getLogger(__name__)


class IndexDomain(Domain):
    """Mathematics domain."""
    name = 'index'
    label = 'index'

    @property
    def entries(self) -> Dict[str, List[Tuple[str, str, str, str, str]]]:
        return self.data.setdefault('entries', {})

    def clear_doc(self, docname: str) -> None:
        self.entries.pop(docname, None)

    def merge_domaindata(self, docnames: Iterable[str], otherdata: Dict) -> None:
        for docname in docnames:
            self.entries[docname] = otherdata['entries'][docname]

    def process_doc(self, env: BuildEnvironment, docname: str, document: Node) -> None:
        """Process a document after it is read by the environment."""
        entries = self.entries.setdefault(env.docname, [])
        for node in document.traverse(addnodes.index):
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
    app.add_domain(IndexDomain)

    return {
        'version': 'builtin',
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
