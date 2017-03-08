# -*- coding: utf-8 -*-
"""
    sphinx.factory
    ~~~~~~~~~~~~~~

    Sphinx component factory.

    Gracefully adapted from the TextPress system by Armin.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function
from pkg_resources import iter_entry_points

from sphinx.errors import ExtensionError, SphinxError
from sphinx.extension import load_extension
from sphinx.locale import _

if False:
    # For type annotation
    from typing import Dict, Type  # NOQA
    from sphinx.application import Sphinx  # NOQA
    from sphinx.builders import Builder  # NOQA


class SphinxFactory(object):
    def __init__(self):
        self.builders = {}  # type: Dict[unicode, Type[Builder]]

    def add_builder(self, builder):
        # type: (Type[Builder]) -> None
        if not hasattr(builder, 'name'):
            raise ExtensionError(_('Builder class %s has no "name" attribute') % builder)
        if builder.name in self.builders:
            raise ExtensionError(_('Builder %r already exists (in module %s)') %
                                 (builder.name, self.builders[builder.name].__module__))
        self.builders[builder.name] = builder

    def preload_builder(self, app, name):
        # type: (Sphinx, unicode) -> None
        if name is None:
            return

        if name not in self.builders:
            entry_points = iter_entry_points('sphinx.builders', name)
            try:
                entry_point = next(entry_points)
            except StopIteration:
                raise SphinxError(_('Builder name %s not registered or available'
                                    ' through entry point') % name)
            load_extension(app, entry_point.module_name)

    def create_builder(self, app, name):
        # type: (Sphinx, unicode) -> Builder
        if name not in self.builders:
            raise SphinxError(_('Builder name %s not registered') % name)

        return self.builders[name](app)
