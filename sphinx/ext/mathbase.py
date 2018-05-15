# -*- coding: utf-8 -*-
"""
    sphinx.ext.mathbase
    ~~~~~~~~~~~~~~~~~~~

    Set up math support in source files and LaTeX/text output.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from docutils import nodes

from sphinx.addnodes import math, math_block as displaymath
from sphinx.config import string_classes
from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.domains.math import MathDomain  # NOQA  # to keep compatibility
from sphinx.locale import __
from sphinx.roles import XRefRole
from sphinx.util import logging

if False:
    # For type annotation
    from typing import Any, Callable, List, Tuple  # NOQA
    from docutils.writers.html4css1 import Writer  # NOQA
    from sphinx.application import Sphinx  # NOQA

logger = logging.getLogger(__name__)


class eqref(nodes.Inline, nodes.TextElement):
    pass


class EqXRefRole(XRefRole):
    def result_nodes(self, document, env, node, is_ref):
        # type: (nodes.Node, BuildEnvironment, nodes.Node, bool) -> Tuple[List[nodes.Node], List[nodes.Node]]  # NOQA
        node['refdomain'] = 'math'
        return [node], []


def get_node_equation_number(writer, node):
    # type: (Writer, nodes.Node) -> unicode
    if writer.builder.config.math_numfig and writer.builder.config.numfig:
        figtype = 'displaymath'
        if writer.builder.name == 'singlehtml':
            key = u"%s/%s" % (writer.docnames[-1], figtype)
        else:
            key = figtype

        id = node['ids'][0]
        number = writer.builder.fignumbers.get(key, {}).get(id, ())
        number = '.'.join(map(str, number))
    else:
        number = node['number']

    return number


def wrap_displaymath(math, label, numbering):
    # type: (unicode, unicode, bool) -> unicode
    def is_equation(part):
        # type: (unicode) -> unicode
        return part.strip()

    if label is None:
        labeldef = ''
    else:
        labeldef = r'\label{%s}' % label
        numbering = True

    parts = list(filter(is_equation, math.split('\n\n')))
    equations = []
    if len(parts) == 0:
        return ''
    elif len(parts) == 1:
        if numbering:
            begin = r'\begin{equation}' + labeldef
            end = r'\end{equation}'
        else:
            begin = r'\begin{equation*}' + labeldef
            end = r'\end{equation*}'
        equations.append('\\begin{split}%s\\end{split}\n' % parts[0])
    else:
        if numbering:
            begin = r'\begin{align}%s\!\begin{aligned}' % labeldef
            end = r'\end{aligned}\end{align}'
        else:
            begin = r'\begin{align*}%s\!\begin{aligned}' % labeldef
            end = r'\end{aligned}\end{align*}'
        for part in parts:
            equations.append('%s\\\\\n' % part.strip())

    return '%s\n%s%s' % (begin, ''.join(equations), end)


def is_in_section_title(node):
    # type: (nodes.Node) -> bool
    """Determine whether the node is in a section title"""
    from sphinx.util.nodes import traverse_parent

    warnings.warn('is_in_section_title() is deprecated.',
                  RemovedInSphinx30Warning)

    for ancestor in traverse_parent(node):
        if isinstance(ancestor, nodes.title) and \
           isinstance(ancestor.parent, nodes.section):
            return True
    return False


def latex_visit_eqref(self, node):
    # type: (nodes.NodeVisitor, eqref) -> None
    label = "equation:%s:%s" % (node['docname'], node['target'])
    eqref_format = self.builder.config.math_eqref_format
    if eqref_format:
        try:
            ref = '\\ref{%s}' % label
            self.body.append(eqref_format.format(number=ref))
        except KeyError as exc:
            logger.warning(__('Invalid math_eqref_format: %r'), exc,
                           location=node)
            self.body.append('\\eqref{%s}' % label)
    else:
        self.body.append('\\eqref{%s}' % label)
    raise nodes.SkipNode


def setup_math(app, htmlinlinevisitors, htmldisplayvisitors):
    # type: (Sphinx, Tuple[Callable, Any], Tuple[Callable, Any]) -> None
    app.add_config_value('math_eqref_format', None, 'env', string_classes)
    app.add_config_value('math_numfig', True, 'env')
    app.add_node(math, override=True,
                 html=htmlinlinevisitors)
    app.add_node(displaymath, override=True,
                 html=htmldisplayvisitors)
    app.add_node(eqref, latex=(latex_visit_eqref, None))
    app.add_role('eq', EqXRefRole(warn_dangling=True))
