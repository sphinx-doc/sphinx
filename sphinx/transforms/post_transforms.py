# -*- coding: utf-8 -*-
"""
    sphinx.transforms.post_transforms
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx import addnodes
from sphinx.environment import NoUri
from sphinx.transforms import SphinxTransform

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


class ReferencesResolver(SphinxTransform):
    """
    Resolves cross-references on doctrees.
    """

    default_priority = 10

    def apply(self):
        # type: () -> None
        for node in self.document.traverse(addnodes.pending_xref):
            contnode = node[0].deepcopy()
            newnode = None

            typ = node['reftype']
            target = node['reftarget']
            refdoc = node.get('refdoc', self.env.docname)
            domain = None

            try:
                if 'refdomain' in node and node['refdomain']:
                    # let the domain try to resolve the reference
                    try:
                        domain = self.env.domains[node['refdomain']]
                    except KeyError:
                        raise NoUri
                    newnode = domain.resolve_xref(self.env, refdoc, self.app.builder,
                                                  typ, target, node, contnode)
                # really hardwired reference types
                elif typ == 'any':
                    newnode = self.env._resolve_any_reference(self.app.builder, refdoc,
                                                              node, contnode)
                # no new node found? try the missing-reference event
                if newnode is None:
                    newnode = self.app.emit_firstresult('missing-reference', self.env,
                                                        node, contnode)
                    # still not found? warn if node wishes to be warned about or
                    # we are in nit-picky mode
                    if newnode is None:
                        self.env._warn_missing_reference(refdoc, typ, target, node, domain)
            except NoUri:
                newnode = contnode
            node.replace_self(newnode or contnode)


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_post_transform(ReferencesResolver)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
