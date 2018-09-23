# -*- coding: utf-8 -*-
"""
    sphinx.util.typing
    ~~~~~~~~~~~~~~~~~~

    The composit types for Sphinx.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Callable, Dict, List, Tuple

from docutils import nodes
from docutils.parsers.rst.states import Inliner
from six import text_type


# common role functions
RoleFunction = Callable[[text_type, text_type, text_type, int, Inliner, Dict, List[text_type]],
                        Tuple[List[nodes.Node], List[nodes.Node]]]

# title getter functions for enumerable nodes (see sphinx.domains.std)
TitleGetter = Callable[[nodes.Node], text_type]
