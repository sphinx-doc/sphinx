# -*- coding: utf-8 -*-
"""
    sphinx.util.images
    ~~~~~~~~~~~

    Image utility functions for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import imagesize

try:
    from PIL import Image        # check for the Python Imaging Library
except ImportError:
    try:
        import Image
    except ImportError:
        Image = None


def get_image_size(filename):
    try:
        size = imagesize.get(filename)
        if size[0] == -1:
            size = None

        if size is None and Image:  # fallback to PIL
            im = Image.open(filename)
            size = im.size
            try:
                im.fp.close()
            except Exception:
                pass

        return size
    except:
        return None
