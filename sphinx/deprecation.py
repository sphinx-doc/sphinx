# -*- coding: utf-8 -*-
"""
    sphinx.deprecation
    ~~~~~~~~~~~~~~~~~~

    Sphinx deprecation classes and utilities.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""


class RemovedInSphinx16Warning(DeprecationWarning):
    pass


class RemovedInSphinx17Warning(PendingDeprecationWarning):
    pass


RemovedInNextVersionWarning = RemovedInSphinx16Warning
