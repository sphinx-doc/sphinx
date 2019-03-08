"""
    sphinx.environment.adapters.asset
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Assets adapter for sphinx.environment.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

if False:
    # For type annotation
    from sphinx.environment import BuildEnvironment  # NOQA


class ImageAdapter:
    def __init__(self, env):
        # type: (BuildEnvironment) -> None
        self.env = env

    def get_original_image_uri(self, name):
        # type: (str) -> str
        """Get the original image URI."""
        while name in self.env.original_image_uri:
            name = self.env.original_image_uri[name]

        return name
