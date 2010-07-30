# -*- coding: utf-8 -*-
"""
    sphinx.websupport.errors
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Contains Error classes for the web support package.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

__all__ = ['DocumentNotFoundError', 'SrcdirNotSpecifiedError']

class DocumentNotFoundError(Exception):
    pass


class SrcdirNotSpecifiedError(Exception):
    pass
