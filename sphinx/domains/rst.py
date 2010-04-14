# -*- coding: utf-8 -*-
"""
    sphinx.domains.rst
    ~~~~~~~~~~~~~~~~~~

    The reStructuredText domain.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.locale import l_, _
from sphinx.directives import ObjectDescription
from sphinx.domains.python import py_paramlist_re as js_paramlist_re
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.util.docfields import Field, GroupedField, TypedField

class ReSTDirective(ObjectDescription):
    pass

class ReSTRole(ObjectDescription):
    pass
    
class ReSTXRefRole(XRefRole):
    pass

class ReSTDomain(Domain):
    """ReStructuredText domain."""
    name = 'rst'
    label = 'reStructuredText'
    
    object_types = {
        'directive': ObjType(l_('reStructuredText directive'), 'dir'),
        'role':      ObjType(l_('reStructuredText role'),      'role'),
    }
    directives = {
        'directive': ReSTDirective,
        'role':      ReSTRole,
    }
    roles = {
        'dir':  ReSTXRefRole(),
        'role': ReSTXRefRole(),
    }
    





