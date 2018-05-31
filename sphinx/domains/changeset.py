# -*- coding: utf-8 -*-
"""
    sphinx.domains.changeset
    ~~~~~~~~~~~~~~~~~~~~~~~~

    The changeset domain.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import NamedTuple

from six import iteritems

from sphinx.domains import Domain


if False:
    # For type annotation
    from typing import Any, Dict, List  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA


ChangeSet = NamedTuple('ChangeSet', [('type', str),
                                     ('docname', str),
                                     ('lineno', int),
                                     ('module', str),
                                     ('descname', str),
                                     ('content', str)])


class ChangeSetDomain(Domain):
    """Domain for changesets."""

    name = 'changeset'
    label = 'changeset'

    initial_data = {
        'changes': {},      # version -> list of ChangeSet
    }  # type: Dict

    def clear_doc(self, docname):
        # type: (unicode) -> None
        for version, changes in iteritems(self.data['changes']):
            for changeset in changes[:]:
                if changeset.docname == docname:
                    changes.remove(changeset)

    def merge_domaindata(self, docnames, otherdata):
        # type: (List[unicode], Dict) -> None
        # XXX duplicates?
        for version, otherchanges in iteritems(otherdata['changes']):
            changes = self.data['changes'].setdefault(version, [])
            for changeset in otherchanges:
                if changeset.docname in docnames:
                    changes.append(changeset)

    def process_doc(self, env, docname, document):
        # type: (BuildEnvironment, unicode, nodes.Node) -> None
        pass  # nothing to do here. All changesets are registered on calling directive.

    def note_changeset(self, node):
        # type: (nodes.Node) -> None
        version = node['version']
        module = self.env.ref_context.get('py:module')
        objname = self.env.temp_data.get('object')
        changeset = ChangeSet(node['type'], self.env.docname, node.line,  # type: ignore
                              module, objname, node.astext())
        self.data['changes'].setdefault(version, []).append(changeset)

    def get_changesets_for(self, version):
        # type: (unicode) -> List[ChangeSet]
        return self.data['changes'].get(version, [])


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_domain(ChangeSetDomain)

    return {
        'version': 'builtin',
        'env_version': 1,
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
