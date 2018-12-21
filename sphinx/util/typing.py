"""
    sphinx.util.typing
    ~~~~~~~~~~~~~~~~~~

    The composit types for Sphinx.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from typing import Any, Callable, Dict, List, Tuple, Union

from docutils import nodes
from docutils.parsers.rst.states import Inliner
from six import text_type


# An entry of Directive.option_spec
DirectiveOption = Callable[[str], Any]

# Text like nodes which are initialized with text and rawsource
TextlikeNode = Union[nodes.Text, nodes.TextElement]

# common role functions
RoleFunction = Callable[[text_type, text_type, text_type, int, Inliner, Dict, List[text_type]],
                        Tuple[List[nodes.Node], List[nodes.system_message]]]

# title getter functions for enumerable nodes (see sphinx.domains.std)
TitleGetter = Callable[[nodes.Node], text_type]

# inventory data on memory
Inventory = Dict[str, Dict[str, Tuple[str, str, str, str]]]
