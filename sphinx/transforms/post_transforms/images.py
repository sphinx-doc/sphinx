# -*- coding: utf-8 -*-
"""
    sphinx.transforms.post_transforms.images
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils transforms used by Sphinx.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from hashlib import sha1

from six import text_type
from docutils import nodes

from sphinx.transforms import SphinxTransform
from sphinx.util import logging, requests
from sphinx.util.images import guess_mimetype, get_image_extension, parse_data_uri
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

    @property
    def imagedir(self):
        # type: () -> unicode
        return os.path.join(self.app.doctreedir, 'images')


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
        basename = os.path.basename(node['uri'])
        if '?' in basename:
            basename = basename.split('?')[0]
        dirname = node['uri'].replace('://', '/').translate({ord("?"): u"/",
                                                             ord("&"): u"/"})
        ensuredir(os.path.join(self.imagedir, dirname))
        path = os.path.join(self.imagedir, dirname, basename)
        try:
            r = requests.get(node['uri'])
            if r.status_code != 200:
                logger.warning('Could not fetch remote image: %s [%d]' %
                               (node['uri'], r.status_code))
            else:
                self.app.env.original_image_uri[path] = node['uri']

                with open(path, 'wb') as f:
                    f.write(r.content)

                mimetype = guess_mimetype(path, default='*')
                node['candidates'].pop('?')
                node['candidates'][mimetype] = path
                node['uri'] = path
                self.app.env.images.add_file(self.env.docname, path)
        except Exception as exc:
            logger.warning('Could not fetch remote image: %s [%s]' %
                           (node['uri'], text_type(exc)))


class DataURIExtractor(BaseImageConverter):
    default_priority = 150

    def match(self, node):
        # type: (nodes.Node) -> bool
        if self.app.builder.supported_data_uri_images:
            return False
        else:
            return 'data:' in node['uri']

    def handle(self, node):
        # type: (nodes.Node) -> None
        image = parse_data_uri(node['uri'])
        ext = get_image_extension(image.mimetype)
        if ext is None:
            logger.warning('Unknown image format: %s...', node['uri'][:32],
                           location=node)
            return

        ensuredir(os.path.join(self.imagedir, 'embeded'))
        digest = sha1(image.data).hexdigest()
        path = os.path.join(self.imagedir, 'embeded', digest + ext)
        self.app.env.original_image_uri[path] = node['uri']

        with open(path, 'wb') as f:
            f.write(image.data)

        node['candidates'].pop('?')
        node['candidates'][image.mimetype] = path
        node['uri'] = path
        self.app.env.images.add_file(self.env.docname, path)


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_post_transform(ImageDownloader)
    app.add_post_transform(DataURIExtractor)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
