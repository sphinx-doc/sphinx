# -*- coding: utf-8 -*-
"""
    sphinx.builders.websupport
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Builder for the web support package.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinxcontrib.websupport.builder import WebSupportBuilder

if False:
    # For type annotation
    from typing import Any, Dict  # NOQA
    from sphinx.application import Sphinx  # NOQA


def setup(app):
    # type: (Sphinx) -> Dict[unicode, Any]
    app.add_builder(WebSupportBuilder)

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
