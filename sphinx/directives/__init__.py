# -*- coding: utf-8 -*-
"""
    sphinx.directives
    ~~~~~~~~~~~~~~~~~

    Handlers for additional ReST directives.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from docutils.parsers.rst import directives
from docutils.parsers.rst.directives import images

# import and register directives
from sphinx.directives.desc import *
from sphinx.directives.code import *
from sphinx.directives.other import *


# allow units for the figure's "figwidth"
try:
    images.Figure.option_spec['figwidth'] = \
        directives.length_or_percentage_or_unitless
except AttributeError:
    images.figure.options['figwidth'] = \
        directives.length_or_percentage_or_unitless
