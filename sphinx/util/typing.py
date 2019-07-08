"""
    sphinx.util.typing
    ~~~~~~~~~~~~~~~~~~

    The composit types for Sphinx.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Any, Callable, Dict, List, Tuple, Union

from docutils import nodes
from docutils.parsers.rst.states import Inliner


# An entry of Directive.option_spec
DirectiveOption = Callable[[str], Any]

# Text like nodes which are initialized with text and rawsource
TextlikeNode = Union[nodes.Text, nodes.TextElement]

# type of None
NoneType = type(None)

# path matcher
PathMatcher = Callable[[str], bool]

# common role functions
RoleFunction = Callable[[str, str, str, int, Inliner, Dict[str, Any], List[str]],
                        Tuple[List[nodes.Node], List[nodes.system_message]]]

# title getter functions for enumerable nodes (see sphinx.domains.std)
TitleGetter = Callable[[nodes.Node], str]

# inventory data on memory
Inventory = Dict[str, Dict[str, Tuple[str, str, str, str]]]
