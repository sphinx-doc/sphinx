"""
    sphinx.ext.mathbase
    ~~~~~~~~~~~~~~~~~~~

    Set up math support in source files and LaTeX/text output.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings
from typing import Callable, List, Tuple

from docutils import nodes
from docutils.nodes import Element, Node
from docutils.parsers.rst.roles import math_role as math_role_base

from sphinx.addnodes import math, math_block as displaymath  # NOQA  # to keep compatibility
from sphinx.application import Sphinx
from sphinx.builders.latex.nodes import math_reference as eqref  # NOQA  # to keep compatibility
from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.directives.patches import MathDirective as MathDirectiveBase
from sphinx.domains.math import MathDomain  # NOQA  # to keep compatibility
from sphinx.domains.math import MathReferenceRole as EqXRefRole  # NOQA  # to keep compatibility
from sphinx.writers.html import HTMLTranslator


class MathDirective(MathDirectiveBase):
    def run(self) -> List[Node]:
        warnings.warn('sphinx.ext.mathbase.MathDirective is moved to '
                      'sphinx.directives.patches package.',
                      RemovedInSphinx30Warning, stacklevel=2)
        return super().run()


def math_role(role, rawtext, text, lineno, inliner, options={}, content=[]):
    warnings.warn('sphinx.ext.mathbase.math_role() is deprecated. '
                  'Please use docutils.parsers.rst.roles.math_role() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    return math_role_base(role, rawtext, text, lineno, inliner, options, content)


def get_node_equation_number(writer: HTMLTranslator, node: nodes.math_block) -> str:
    warnings.warn('sphinx.ext.mathbase.get_node_equation_number() is moved to '
                  'sphinx.util.math package.',
                  RemovedInSphinx30Warning, stacklevel=2)
    from sphinx.util.math import get_node_equation_number
    return get_node_equation_number(writer, node)


def wrap_displaymath(text: str, label: str, numbering: bool) -> str:
    warnings.warn('sphinx.ext.mathbase.wrap_displaymath() is moved to '
                  'sphinx.util.math package.',
                  RemovedInSphinx30Warning, stacklevel=2)
    from sphinx.util.math import wrap_displaymath
    return wrap_displaymath(text, label, numbering)


def is_in_section_title(node: Element) -> bool:
    """Determine whether the node is in a section title"""
    from sphinx.util.nodes import traverse_parent

    warnings.warn('is_in_section_title() is deprecated.',
                  RemovedInSphinx30Warning, stacklevel=2)

    for ancestor in traverse_parent(node):
        if isinstance(ancestor, nodes.title) and \
           isinstance(ancestor.parent, nodes.section):
            return True
    return False


def setup_math(app: Sphinx,
               htmlinlinevisitors: Tuple[Callable, Callable],
               htmldisplayvisitors: Tuple[Callable, Callable]) -> None:
    warnings.warn('setup_math() is deprecated. '
                  'Please use app.add_html_math_renderer() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)

    app.add_html_math_renderer('unknown', htmlinlinevisitors, htmldisplayvisitors)
