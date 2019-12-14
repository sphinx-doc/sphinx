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
from sphinx.writers.latex import LaTeXTranslator
from sphinx.writers.manpage import ManualPageTranslator
from sphinx.writers.texinfo import TexinfoTranslator
from sphinx.writers.text import TextTranslator


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


def latex_visit_math(self: LaTeXTranslator, node: Element) -> None:
    warnings.warn('latex_visit_math() is deprecated. '
                  'Please use LaTeXTranslator.visit_math() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math(node)


def latex_visit_displaymath(self: LaTeXTranslator, node: Element) -> None:
    warnings.warn('latex_visit_displaymath() is deprecated. '
                  'Please use LaTeXTranslator.visit_math_block() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math_block(node)


def man_visit_math(self: ManualPageTranslator, node: Element) -> None:
    warnings.warn('man_visit_math() is deprecated. '
                  'Please use ManualPageTranslator.visit_math() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math(node)


def man_visit_displaymath(self: ManualPageTranslator, node: Element) -> None:
    warnings.warn('man_visit_displaymath() is deprecated. '
                  'Please use ManualPageTranslator.visit_math_block() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math_block(node)


def man_depart_displaymath(self: ManualPageTranslator, node: Element) -> None:
    warnings.warn('man_depart_displaymath() is deprecated. '
                  'Please use ManualPageTranslator.depart_math_block() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.depart_math_block(node)


def texinfo_visit_math(self: TexinfoTranslator, node: Element) -> None:
    warnings.warn('texinfo_visit_math() is deprecated. '
                  'Please use TexinfoTranslator.visit_math() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math(node)


def texinfo_visit_displaymath(self: TexinfoTranslator, node: Element) -> None:
    warnings.warn('texinfo_visit_displaymath() is deprecated. '
                  'Please use TexinfoTranslator.visit_math_block() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math_block(node)


def texinfo_depart_displaymath(self: TexinfoTranslator, node: Element) -> None:
    warnings.warn('texinfo_depart_displaymath() is deprecated. '
                  'Please use TexinfoTranslator.depart_math_block() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)


def text_visit_math(self: TextTranslator, node: Element) -> None:
    warnings.warn('text_visit_math() is deprecated. '
                  'Please use TextTranslator.visit_math() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math(node)


def text_visit_displaymath(self: TextTranslator, node: Element) -> None:
    warnings.warn('text_visit_displaymath() is deprecated. '
                  'Please use TextTranslator.visit_math_block() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)
    self.visit_math_block(node)


def setup_math(app: Sphinx,
               htmlinlinevisitors: Tuple[Callable, Callable],
               htmldisplayvisitors: Tuple[Callable, Callable]) -> None:
    warnings.warn('setup_math() is deprecated. '
                  'Please use app.add_html_math_renderer() instead.',
                  RemovedInSphinx30Warning, stacklevel=2)

    app.add_html_math_renderer('unknown', htmlinlinevisitors, htmldisplayvisitors)
