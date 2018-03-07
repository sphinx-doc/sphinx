# -*- coding: utf-8 -*-
"""
    sphinx.environment.adapters.asset
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Assets adapter for sphinx.environment.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment  # NOQA


class ImageAdapter(object):
    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        self.env = env

    def get_original_image_uri(self, name):
        # type: (unicode) -> unicode
        """Get the original image URI."""
        while name in self.env.original_image_uri:
            name = self.env.original_image_uri[name]

        return name
