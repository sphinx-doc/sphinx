# -*- coding: utf-8 -*-
"""
    sphinx.environment.managers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Manager components for sphinx.environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

if False:
    # For type annotation
    from typing import Any  # NOQA
    from docutils import nodes  # NOQA
    from sphinx.environment import BuildEnvironment  # NOQA


class EnvironmentManager(object):
    """Base class for sphinx.environment managers."""
    name = None  # type: unicode
    env = None  # type: BuildEnvironment

    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        self.env = env

    def attach(self, env):
        # type: (BuildEnvironment) -> None
        self.env = env
        if self.name:
            setattr(env, self.name, self)

    def detach(self, env):
        # type: (BuildEnvironment) -> None
        self.env = None
        if self.name:
            delattr(env, self.name)

    def clear_doc(self, docname):
        # type: (unicode) -> None
        raise NotImplementedError

    def merge_other(self, docnames, other):
        # type: (List[unicode], Any) -> None
        raise NotImplementedError

    def process_doc(self, docname, doctree):
        # type: (unicode, nodes.Node) -> None
        raise NotImplementedError
