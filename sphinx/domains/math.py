"""
    sphinx.domains.math
    ~~~~~~~~~~~~~~~~~~~

    The math domain.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import warnings

from docutils import nodes
from docutils.nodes import make_id

from sphinx.deprecation import RemovedInSphinx40Warning
from sphinx.domains import Domain
from sphinx.locale import __
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.nodes import make_refnode

if False:
    # For type annotation
    from typing import Any, Dict, Iterable, List, Tuple  # NOQA
    from sphinx import addnodes  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.builders import Builder  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA

logger = logging.getLogger(__name__)


class MathReferenceRole(XRefRole):
    def result_nodes(self, document, env, node, is_ref):
        # type: (nodes.document, BuildEnvironment, nodes.Element, bool) -> Tuple[List[nodes.Node], List[nodes.system_message]]  # NOQA
        node['refdomain'] = 'math'
        return [node], []


class MathDomain(Domain):
    """Mathematics domain."""
    name = 'math'
    label = 'mathematics'

    initial_data = {
        'objects': {},  # labelid -> (docname, eqno)
        'has_equations': {},  # docname -> bool
    }  # type: Dict
    dangling_warnings = {
        'eq': 'equation not found: %(target)s',
    }
    enumerable_nodes = {  # node_class -> (figtype, title_getter)
        nodes.math_block: ('displaymath', None),
    }
    roles = {
        'numref': MathReferenceRole(),
    }

    @property
    def equations(self):
        # type: () -> Dict[str, Tuple[str, int]]
        return self.data.setdefault('objects', {})  # labelid -> (docname, eqno)

    def note_equation(self, docname, labelid, location=None):
        # type: (str, str, Any) -> None
        if labelid in self.equations:
            other = self.equations[labelid][0]
            logger.warning(__('duplicate label of equation %s, other instance in %s') %
                           (labelid, other), location=location)

        self.equations[labelid] = (docname, self.env.new_serialno('eqno') + 1)

    def get_equation_number_for(self, labelid):
        # type: (str) -> int
        if labelid in self.equations:
            return self.equations[labelid][1]
        else:
            return None

    def process_doc(self, env, docname, document):
        # type: (BuildEnvironment, str, nodes.document) -> None
        def math_node(node):
            # type: (nodes.Node) -> bool
            return isinstance(node, (nodes.math, nodes.math_block))

        self.data['has_equations'][docname] = any(document.traverse(math_node))

    def clear_doc(self, docname):
        # type: (str) -> None
        for equation_id, (doc, eqno) in list(self.equations.items()):
            if doc == docname:
                del self.equations[equation_id]

        self.data['has_equations'].pop(docname, None)

    def merge_domaindata(self, docnames, otherdata):
        # type: (Iterable[str], Dict) -> None
        for labelid, (doc, eqno) in otherdata['objects'].items():
            if doc in docnames:
                self.equations[labelid] = (doc, eqno)

        for docname in docnames:
            self.data['has_equations'][docname] = otherdata['has_equations'][docname]

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        # type: (BuildEnvironment, str, Builder, str, str, addnodes.pending_xref, nodes.Element) -> nodes.Element  # NOQA
        assert typ in ('eq', 'numref')
        docname, number = self.equations.get(target, (None, None))
        if docname:
            # TODO: perhaps use rather a sphinx-core provided prefix here?
            node_id = make_id('equation-%s' % target)
            if env.config.math_numfig and env.config.numfig:
                if docname in env.toc_fignumbers:
                    numbers = env.toc_fignumbers[docname]['displaymath'].get(node_id, ())
                    eqno = '.'.join(map(str, numbers))
                else:
                    eqno = ''
            else:
                eqno = str(number)

            try:
                eqref_format = env.config.math_eqref_format or "({number})"
                title = nodes.Text(eqref_format.format(number=eqno))
            except KeyError as exc:
                logger.warning(__('Invalid math_eqref_format: %r'), exc,
                               location=node)
                title = nodes.Text("(%d)" % number)
                title = nodes.Text("(%d)" % number)
            return make_refnode(builder, fromdocname, docname, node_id, title)
        else:
            return None

    def resolve_any_xref(self, env, fromdocname, builder, target, node, contnode):
        # type: (BuildEnvironment, str, Builder, str, addnodes.pending_xref, nodes.Element) -> List[Tuple[str, nodes.Element]]  # NOQA
        refnode = self.resolve_xref(env, fromdocname, builder, 'eq', target, node, contnode)
        if refnode is None:
            return []
        else:
            return [('eq', refnode)]

    def get_objects(self):
        # type: () -> List
        return []

    def add_equation(self, env, docname, labelid):
        # type: (BuildEnvironment, str, str) -> int
        warnings.warn('MathDomain.add_equation() is deprecated.',
                      RemovedInSphinx40Warning)
        if labelid in self.equations:
            path = env.doc2path(self.equations[labelid][0])
            msg = __('duplicate label of equation %s, other instance in %s') % (labelid, path)
            raise UserWarning(msg)
        else:
            eqno = self.get_next_equation_number(docname)
            self.equations[labelid] = (docname, eqno)
            return eqno

    def get_next_equation_number(self, docname):
        # type: (str) -> int
        warnings.warn('MathDomain.get_next_equation_number() is deprecated.',
                      RemovedInSphinx40Warning)
        targets = [eq for eq in self.equations.values() if eq[0] == docname]
        return len(targets) + 1

    def has_equations(self):
        # type: () -> bool
        return any(self.data['has_equations'].values())


def setup(app):
    # type: (Sphinx) -> Dict[str, Any]
    app.add_domain(MathDomain)
    app.add_role('eq', MathReferenceRole(warn_dangling=True))

    return {
        'version': 'builtin',
        'env_version': 2,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
