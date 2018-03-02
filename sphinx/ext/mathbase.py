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
from docutils.nodes import make_id

from sphinx.addnodes import math, math_block as displaymath
from sphinx.config import string_classes
from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.domains import Domain
from sphinx.locale import __
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_refnode

if False:
    # For type annotation
    from typing import Any, Callable, Dict, Iterable, List, Tuple  # NOQA
    from docutils.writers.html4css1 import Writer  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


class eqref(nodes.Inline, nodes.TextElement):
    pass


class EqXRefRole(XRefRole):
    def result_nodes(self, document, env, node, is_ref):
        # type: (nodes.Node, BuildEnvironment, nodes.Node, bool) -> Tuple[List[nodes.Node], List[nodes.Node]]  # NOQA
        node['refdomain'] = 'math'
        return [node], []


class MathDomain(Domain):
    """Mathematics domain."""
    name = 'math'
    label = 'mathematics'

    initial_data = {
        'objects': {},  # labelid -> (docname, eqno)
    }  # type: Dict[unicode, Dict[unicode, Tuple[unicode, int]]]
    dangling_warnings = {
        'eq': 'equation not found: %(target)s',
    }
    enumerable_nodes = {  # node_class -> (figtype, title_getter)
        displaymath: ('displaymath', None),
        nodes.math_block: ('displaymath', None),
    }  # type: Dict[nodes.Node, Tuple[unicode, Callable]]

    def clear_doc(self, docname):
        # type: (unicode) -> None
        for equation_id, (doc, eqno) in list(self.data['objects'].items()):
            if doc == docname:
                del self.data['objects'][equation_id]

    def merge_domaindata(self, docnames, otherdata):
        # type: (Iterable[unicode], Dict) -> None
        for labelid, (doc, eqno) in otherdata['objects'].items():
            if doc in docnames:
                self.data['objects'][labelid] = (doc, eqno)

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        # type: (BuildEnvironment, unicode, Builder, unicode, unicode, nodes.Node, nodes.Node) -> nodes.Node  # NOQA
        assert typ == 'eq'
        docname, number = self.data['objects'].get(target, (None, None))
        if docname:
            if builder.name == 'latex':
                newnode = eqref('', **node.attributes)
                newnode['docname'] = docname
                newnode['target'] = target
                return newnode
            else:
                # TODO: perhaps use rather a sphinx-core provided prefix here?
                node_id = make_id('equation-%s' % target)
                if env.config.math_numfig and env.config.numfig:
                    if docname in env.toc_fignumbers:
                        number = env.toc_fignumbers[docname]['displaymath'].get(node_id, ())
                        number = '.'.join(map(str, number))
                    else:
                        number = ''
                try:
                    eqref_format = env.config.math_eqref_format or "({number})"
                    title = nodes.Text(eqref_format.format(number=number))
                except KeyError as exc:
                    logger.warning(__('Invalid math_eqref_format: %r'), exc,
                                   location=node)
                    title = nodes.Text("(%d)" % number)
                    title = nodes.Text("(%d)" % number)
                return make_refnode(builder, fromdocname, docname, node_id, title)
        else:
            return None

    def resolve_any_xref(self, env, fromdocname, builder, target, node, contnode):
        # type: (BuildEnvironment, unicode, Builder, unicode, nodes.Node, nodes.Node) -> List[nodes.Node]  # NOQA
        refnode = self.resolve_xref(env, fromdocname, builder, 'eq', target, node, contnode)
        if refnode is None:
            return []
        else:
            return [refnode]

    def get_objects(self):
        # type: () -> List
        return []

    def add_equation(self, env, docname, labelid):
        # type: (BuildEnvironment, unicode, unicode) -> int
        equations = self.data['objects']
        if labelid in equations:
            path = env.doc2path(equations[labelid][0])
            msg = __('duplicate label of equation %s, other instance in %s') % (labelid, path)
            raise UserWarning(msg)
        else:
            eqno = self.get_next_equation_number(docname)
            equations[labelid] = (docname, eqno)
            return eqno

    def get_next_equation_number(self, docname):
        # type: (unicode) -> int
        targets = [eq for eq in self.data['objects'].values() if eq[0] == docname]
        return len(targets) + 1


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
    app.add_domain(MathDomain)
    app.add_node(math, override=True,
                 html=htmlinlinevisitors)
    app.add_node(displaymath, override=True,
                 html=htmldisplayvisitors)
    app.add_node(eqref, latex=(latex_visit_eqref, None))
    app.add_role('eq', EqXRefRole(warn_dangling=True))
