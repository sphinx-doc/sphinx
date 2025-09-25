from __future__ import annotations

import sys
import warnings
from typing import TYPE_CHECKING

from docutils import nodes

from sphinx import addnodes
from sphinx.domains.cpp._ids import (
    _id_char_from_prefix,
    _id_explicit_cast,
    _id_fundamental_v1,
    _id_fundamental_v2,
    _id_operator_unary_v2,
    _id_operator_v1,
    _id_operator_v2,
    _id_prefix,
    _id_shorthands_v1,
    _max_id,
)
from sphinx.util.cfamily import (
    ASTBaseBase,
    ASTBaseParenExprList,
    NoOldIdError,
    UnsupportedMultiCharacterCharLiteral,
    verify_description_mode,
)

if TYPE_CHECKING:
    from typing import Any, ClassVar, Literal

    from docutils.nodes import Element, TextElement

    from sphinx.addnodes import desc_signature
    from sphinx.domains.cpp._symbol import Symbol
    from sphinx.environment import BuildEnvironment
    from sphinx.util.cfamily import (
        ASTAttributeList,
        StringifyTransform,
    )


class ASTBase(ASTBaseBase):
    """Base class for all AST nodes."""
    pass


# Define __all__ for this module
__all__ = ['ASTBase']
