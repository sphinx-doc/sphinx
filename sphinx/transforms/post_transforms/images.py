# -*- coding: utf-8 -*-
"""
    sphinx.transforms.post_transforms.images
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os

from docutils import nodes

from sphinx.transforms import SphinxTransform
from sphinx.util import logging, requests
from sphinx.util.osutil import ensuredir

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


logger = logging.getLogger(__name__)


class BaseImageConverter(SphinxTransform):
    def apply(self):
        # type: () -> None
        for node in self.document.traverse(nodes.image):
            if self.match(node):
                self.handle(node)

    def match(self, node):
        # type: (nodes.Node) -> bool
        return True

    def handle(self, node):
        # type: (nodes.Node) -> None
        pass


class ImageDownloader(BaseImageConverter):
    default_priority = 100

    def match(self, node):
        # type: (nodes.Node) -> bool
        if self.app.builder.supported_remote_images:
            return False
        else:
            return '://' in node['uri']

    def handle(self, node):
        # type: (nodes.Node) -> None
        imgdir = os.path.join(self.app.doctreedir, 'images')
        basename = os.path.basename(node['uri'])
        if '?' in basename:
            basename = basename.split('?')[0]
        dirname = node['uri'].replace('://', '/').translate({ord("?"): u"/",
                                                             ord("&"): u"/"})
        ensuredir(os.path.join(imgdir, dirname))
        path = os.path.join(imgdir, dirname, basename)
        with open(path, 'wb') as f:
            r = requests.get(node['uri'])
            f.write(r.content)

        node['candidates'].pop('?')
        node['candidates']['*'] = path
        node['uri'] = path
        self.app.env.images.add_file(self.env.docname, path)


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_post_transform(ImageDownloader)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
