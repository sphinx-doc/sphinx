"""
    Does foo.svg --> foo.pdf with no change to the file.
"""

import shutil

from sphinx.transforms.post_transforms.images import ImageConverter

if False:
    # For type annotation
    from typing import Any, Dict  # NoQA

    from sphinx.application import Sphinx  # NoQA

class MyConverter(ImageConverter):
    conversion_rules = [
        ('image/svg+xml', 'application/pdf'),
    ]

    def is_available(self):
        # type: () -> bool
        return True

    def convert(self, _from, _to):
        # type: (unicode, unicode) -> bool
        """Mock converts the image from SVG to PDF."""
        shutil.copyfile(_from, _to)
        return True


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_post_transform(MyConverter)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
