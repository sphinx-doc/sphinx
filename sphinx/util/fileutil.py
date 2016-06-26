# -*- coding: utf-8 -*-
"""
    sphinx.util.fileutil
    ~~~~~~~~~~~~~~~~~~~~

    File utility functions for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import codecs
from sphinx.util.osutil import copyfile


def copy_asset_file(source, destination, context={}, renderer=None):
    """Copy an asset file to destination.

    On copying, it expands the template variables if the asset is a template file.

    :param source: The path to source file
    :param destination: The path to destination file or directory
    :param context: The template variables
    :param renderer: The template engine
    """
    if os.path.exists(destination) and os.path.isdir(destination):
        # Use source filename if destination points a directory
        destination = os.path.join(destination, os.path.basename(source))

    if source.lower().endswith('_t'):
        if renderer is None:
            msg = 'Template engine is not initialized. Failed to render %s' % source
            raise RuntimeError(msg)

        with codecs.open(source, 'r', encoding='utf-8') as fsrc:
            with codecs.open(destination[:-2], 'w', encoding='utf-8') as fdst:
                fdst.write(renderer.render_string(fsrc.read(), context))
    else:
        copyfile(source, destination)
