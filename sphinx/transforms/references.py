"""
    sphinx.transforms.references
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils import nodes
from docutils.transforms.references import Substitutions

from sphinx.transforms import SphinxTransform

if False:
    # For type annotation
    from typing import Any  # NOQA


class SubstitutionDefinitionsRemover(SphinxTransform):
    """Remove ``substitution_definition node from doctrees."""

    # should be invoked after Substitutions process
    default_priority = Substitutions.default_priority + 1

    def apply(self, **kwargs):
        # type: (Any) -> None
        for node in self.document.traverse(nodes.substitution_definition):
            node.parent.remove(node)


class SphinxDomains(SphinxTransform):
    """Collect objects to Sphinx domains for cross references."""
    default_priority = 850

    def apply(self, **kwargs):
        # type: (Any) -> None
        for domain in self.env.domains.values():
            domain.process_doc(self.env, self.env.docname, self.document)
