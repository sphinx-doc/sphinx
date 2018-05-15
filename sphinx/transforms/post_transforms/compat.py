# -*- coding: utf-8 -*-
"""
    sphinx.transforms.post_transforms.compat
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Post transforms for compatibility

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import TYPE_CHECKING

from docutils import nodes

from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.transforms import SphinxTransform
from sphinx.util import logging

if TYPE_CHECKING:
    from typing import Any, Callable, Dict, Iterable, List, Tuple  # NOQA
    from docutils.parsers.rst.states import Inliner  # NOQA
    from docutils.writers.html4css1 import Writer  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


class MathNodeMigrator(SphinxTransform):
    """Migrate a math node to docutils'.

    For a long time, Sphinx uses an original node for math. Since 1.8,
    Sphinx starts to use a math node of docutils'.  This transform converts
    old and new nodes to keep compatibility.
    """
    default_priority = 999

    def apply(self):
        # type: () -> None
        for node in self.document.traverse(nodes.math):
            if len(node) == 0:
                # convert an old styled node to new one
                warnings.warn("math node for Sphinx was replaced by docutils'. "
                              "Please use ``docutils.nodes.math`` instead.",
                              RemovedInSphinx30Warning)
                equation = node['latex']
                node += nodes.Text(equation, equation)


def setup(app):
    app.add_post_transform(MathNodeMigrator)
