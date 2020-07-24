"""
    sphinx.transforms.references
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Any, Dict

from docutils import nodes
from docutils.transforms.references import DanglingReferences, Substitutions

from sphinx.transforms import SphinxTransform

if False:
    # For type annotation
    from sphinx.application import Sphinx


class SubstitutionDefinitionsRemover(SphinxTransform):
    """Remove ``substitution_definition node from doctrees."""

    # should be invoked after Substitutions process
    default_priority = Substitutions.default_priority + 1

    def apply(self, **kwargs: Any) -> None:
        for node in self.document.traverse(nodes.substitution_definition):
            node.parent.remove(node)


class SphinxDanglingReferences(DanglingReferences):
    """DanglingReferences transform which does not output info messages."""

    def apply(self, **kwargs: Any) -> None:
        try:
            reporter = self.document.reporter
            report_level = reporter.report_level

            # suppress INFO level messages for a while
            reporter.report_level = max(reporter.WARNING_LEVEL, reporter.report_level)
            super().apply()
        finally:
            reporter.report_level = report_level


class SphinxDomains(SphinxTransform):
    """Collect objects to Sphinx domains for cross references."""
    default_priority = 850

    def apply(self, **kwargs: Any) -> None:
        for domain in self.env.domains.values():
            domain.process_doc(self.env, self.env.docname, self.document)


def setup(app: "Sphinx") -> Dict[str, Any]:
    app.add_transform(SubstitutionDefinitionsRemover)
    app.add_transform(SphinxDanglingReferences)
    app.add_transform(SphinxDomains)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
