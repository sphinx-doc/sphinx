# -*- coding: utf-8 -*-
"""
    sphinx.environment.managers
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Manager components for sphinx.environment.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


class EnvironmentManager(object):
    """Base class for sphinx.environment managers."""
    name = None

    def __init__(self, env):
        self.env = env

    def attach(self, env):
        self.env = env
        if self.name:
            setattr(env, self.name, self)

    def detach(self, env):
        self.env = None
        if self.name:
            delattr(env, self.name)

    def clear_doc(self, docname):
        raise NotImplementedError

    def merge_other(self, docnames, other):
        raise NotImplementedError

    def process_doc(self, docname, doctree):
        raise NotImplementedError
