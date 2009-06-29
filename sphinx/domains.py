# -*- coding: utf-8 -*-
"""
    sphinx.domains
    ~~~~~~~~~~~~~~

    Support for domains, which are groupings of description directives
    describing e.g. constructs of one programming language.

    :copyright: Copyright 2007-2009 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

class Domain(object):
    name = ''
    directives = {}
    label = ''

domains = {}
