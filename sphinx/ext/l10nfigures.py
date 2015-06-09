# -*- coding: utf-8 -*-
"""
    sphinx.ext.l10nfigures
    ~~~~~~~~~~~~~~~~~~~~~~

    Extension to ease the usage of localized images. For all figures, a
    localized version of the pictures will be searched under the name:
    ``image_name-language.extension``. If that one is found, it will be
    used in favor of the original one.

    :copyright: Copyright 2007-2015 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.

"""

import os
import re


def replace_spans(text, spans):
    """ This yield a series of strings """
    if len(spans) == 0:
        yield text
        return
    offset0 = spans[0][0][0]

    yield text[:offset0]
    for i, (span, content) in enumerate(spans):
        yield content
        if i != len(spans) - 1:
            # For all except the last one
            next_offset = spans[i + 1][0][0]
            yield text[span[1]:next_offset]

    last_offset = spans[-1][0][1]
    yield text[last_offset:]


def translate_figures(app, docname, source):
    if app.config.language is None:
        # Do nothing if no localization is asked
        return

    updates = []

    for m in re.finditer(r'\.\. figure::\s+(.+)$', source[0], re.MULTILINE):
        imguri = m.group(1)
        rel_imgpath, full_imgpath = app.env.relfn2path(imguri, docname)
        root, ext = os.path.splitext(full_imgpath)
        l10n_imgpath = '-'.join([root, app.config.language]) + ext
        if os.path.exists(l10n_imgpath):
            # Replace the image path with our one
            app.info("Using [%s] version for %s" % (app.config.language, imguri))
            root, ext = os.path.splitext(imguri)
            updates.append((m.span(1), '-'.join([root, app.config.language]) + ext))

    source[0] = ''.join(s for s in replace_spans(source[0], updates))


def setup(app):
    app.connect('source-read', translate_figures)
