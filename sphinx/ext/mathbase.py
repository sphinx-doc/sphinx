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
from sphinx.builders.latex.nodes import math_reference as eqref  # NOQA  # to keep compatibility
from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.domains.math import MathDomain  # NOQA  # to keep compatibility
from sphinx.domains.math import MathReferenceRole as EqXRefRole  # NOQA  # to keep compatibility

if False:
    # For type annotation
    from typing import Any, Callable, List, Tuple  # NOQA
    from docutils.writers.html4css1 import Writer  # NOQA
    from sphinx.application import Sphinx  # NOQA


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


def setup_math(app, htmlinlinevisitors, htmldisplayvisitors):
    # type: (Sphinx, Tuple[Callable, Any], Tuple[Callable, Any]) -> None
    app.add_node(math, override=True,
                 html=htmlinlinevisitors)
    app.add_node(displaymath, override=True,
                 html=htmldisplayvisitors)
