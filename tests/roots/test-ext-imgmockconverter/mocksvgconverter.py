"""Does foo.svg --> foo.pdf with no change to the file."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from sphinx.transforms.post_transforms.images import ImageConverter

if TYPE_CHECKING:
    import os

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class MyConverter(ImageConverter):
    conversion_rules = [
        ('image/svg+xml', 'application/pdf'),
    ]

    def is_available(self) -> bool:
        return True

    def convert(
        self, _from: str | os.PathLike[str], _to: str | os.PathLike[str]
    ) -> bool:
        """Mock converts the image from SVG to PDF."""
        shutil.copyfile(_from, _to)
        return True


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_post_transform(MyConverter)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
