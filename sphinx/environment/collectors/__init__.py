# -*- coding: utf-8 -*-
"""
    sphinx.environment.collectors
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    The data collector components for sphinx.environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from six import itervalues

if False:
    # For type annotation
    from docutils import nodes  # NOQA
    from sphinx.sphinx import Sphinx  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA


class EnvironmentCollector(object):
    """Base class of data collector for sphinx.environment."""

    listener_ids = None  # type: Dict[unicode, int]

    def enable(self, app):
        # type: (Sphinx) -> None
        assert self.listener_ids is None
        self.listener_ids = {}
        self.listener_ids['doctree-read'] = app.connect('doctree-read', self.process_doc)
        self.listener_ids['env-merge-info'] = app.connect('env-merge-info', self.merge_other)
        self.listener_ids['env-purge-doc'] = app.connect('env-purge-doc', self.clear_doc)

    def disable(self, app):
        # type: (Sphinx) -> None
        assert self.listener_ids is not None
        for listener_id in itervalues(self.listener_ids):
            app.disconnect(listener_id)
        self.listener_ids = None

    def clear_doc(self, app, env, docname):
        # type: (Sphinx, BuildEnvironment, unicode) -> None
        raise NotImplementedError

    def merge_other(self, app, env, docnames, other):
        # type: (Sphinx, BuildEnvironment, Set[unicode], BuildEnvironment) -> None
        raise NotImplementedError

    def process_doc(self, app, doctree):
        # type: (Sphinx, nodes.Node) -> None
        raise NotImplementedError
