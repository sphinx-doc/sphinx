# -*- coding: utf-8 -*-
"""
    sphinx.util.compat_docutils
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Docutils compatibility absorbing layer for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import docutils

if docutils.__version__ < '0.13':
    from sphinx.util.compat_docutils.html5 import Writer, HTMLTranslator
else:
    from docutils.writers.html_plain import Writer, HTMLTranslator

__all__ = ('Writer', 'HTMLTranslator')
