"""
    sphinx.domains.citation
    ~~~~~~~~~~~~~~~~~~~~~~~

    The citation domain.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import cast

from docutils import nodes

from sphinx import addnodes
from sphinx.transforms import SphinxTransform
from sphinx.util.nodes import copy_source_info

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


class CitationDefinitionTransform(SphinxTransform):
    """Mark citation definition labels as not smartquoted."""
    default_priority = 619

    def apply(self, **kwargs):
        # type: (Any) -> None
        for node in self.document.traverse(nodes.citation):
            label = cast(nodes.label, node[0])
            label['support_smartquotes'] = False


class CitationReferenceTransform(SphinxTransform):
    """
    Replace citation references by pending_xref nodes before the default
    docutils transform tries to resolve them.
    """
    default_priority = 619

    def apply(self, **kwargs):
        # type: (Any) -> None
        for node in self.document.traverse(nodes.citation_reference):
            target = node.astext()
            ref = addnodes.pending_xref(target, refdomain='std', reftype='citation',
                                        reftarget=target, refwarn=True,
                                        support_smartquotes=False,
                                        ids=node["ids"],
                                        classes=node.get('classes', []))
            ref += nodes.inline(target, '[%s]' % target)
            copy_source_info(node, ref)
            node.replace_self(ref)


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    app.add_transform(CitationDefinitionTransform)
    app.add_transform(CitationReferenceTransform)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
