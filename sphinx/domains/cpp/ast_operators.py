from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, Literal

from docutils import nodes

from sphinx import addnodes
from sphinx.domains.cpp._ids import (
    _id_operator_v1,
    _id_operator_v2,
)
from sphinx.util.cfamily import (
    NoOldIdError,
    verify_description_mode,
)

if TYPE_CHECKING:
    from docutils.nodes import TextElement

    from sphinx.addnodes import desc_signature
    from sphinx.domains.cpp._symbol import Symbol
    from sphinx.domains.cpp.ast_base import ASTBase
    from sphinx.domains.cpp.ast_names import ASTIdentifier
    from sphinx.domains.cpp.ast_types import ASTType
    from sphinx.environment import BuildEnvironment
    from sphinx.util.cfamily import StringifyTransform

# Import ASTBase for use in this module
from sphinx.domains.cpp.ast_base import ASTBase


class ASTOperator(ASTBase):
    """Base class for operators."""
    is_anonymous: ClassVar[Literal[False]] = False

    def __eq__(self, other: object) -> bool:
        raise NotImplementedError(repr(self))

    def __hash__(self) -> int:
        raise NotImplementedError(repr(self))

    def is_anon(self) -> bool:
        return self.is_anonymous

    def is_operator(self) -> bool:
        return True

    def get_id(self, version: int) -> str:
        raise NotImplementedError

    def _describe_identifier(
        self,
        signode: TextElement,
        identnode: TextElement,
        env: BuildEnvironment,
        symbol: Symbol,
    ) -> None:
        """Render the prefix into signode, and the last part into identnode."""
        raise NotImplementedError

    def describe_signature(
        self,
        signode: TextElement,
        mode: str,
        env: BuildEnvironment,
        prefix: str,
        templateArgs: str,
        symbol: Symbol,
    ) -> None:
        verify_description_mode(mode)
        if mode == 'lastIsName':
            main_name = addnodes.desc_name()
            self._describe_identifier(main_name, main_name, env, symbol)
            signode += main_name
        elif mode == 'markType':
            target_text = prefix + str(self) + templateArgs
            pnode = addnodes.pending_xref(
                '',
                refdomain='cpp',
                reftype='identifier',
                reftarget=target_text,
                modname=None,
                classname=None,
            )
            pnode['cpp:parent_key'] = symbol.get_lookup_key()
            main_name = addnodes.desc_name()
            self._describe_identifier(pnode, main_name, env, symbol)
            pnode += main_name
            signode += pnode
        else:
            raise Exception('Unknown description mode: %s' % mode)


class ASTOperatorBuildIn(ASTOperator):
    """Represents a built-in operator."""

    def __init__(self, op: str) -> None:
        self.op = op

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTOperatorBuildIn):
            return NotImplemented
        return self.op == other.op

    def __hash__(self) -> int:
        return hash(self.op)

    def get_id(self, version: int) -> str:
        if version == 1:
            ids = _id_operator_v1
            if self.op not in ids:
                raise NoOldIdError
        else:
            ids = _id_operator_v2
        if self.op not in ids:
            raise Exception(
                'Internal error: Built-in operator "%s" can not '
                'be mapped to an id.' % self.op
            )
        return ids[self.op]

    def _stringify(self, transform: StringifyTransform) -> str:
        if self.op in {'new', 'new[]', 'delete', 'delete[]'} or self.op[0] in 'abcnox':
            return 'operator ' + self.op
        else:
            return 'operator' + self.op

    def _describe_identifier(
        self,
        signode: TextElement,
        identnode: TextElement,
        env: BuildEnvironment,
        symbol: Symbol,
    ) -> None:
        signode += addnodes.desc_sig_keyword('operator', 'operator')
        if self.op in {'new', 'new[]', 'delete', 'delete[]'} or self.op[0] in 'abcnox':
            signode += addnodes.desc_sig_space()
        identnode += addnodes.desc_sig_operator(self.op, self.op)


class ASTOperatorLiteral(ASTOperator):
    """Represents a user-defined literal operator."""

    def __init__(self, identifier: ASTIdentifier) -> None:
        self.identifier = identifier

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTOperatorLiteral):
            return NotImplemented
        return self.identifier == other.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)

    def get_id(self, version: int) -> str:
        if version == 1:
            raise NoOldIdError
        return 'li' + self.identifier.get_id(version)

    def _stringify(self, transform: StringifyTransform) -> str:
        return 'operator""' + transform(self.identifier)

    def _describe_identifier(
        self,
        signode: TextElement,
        identnode: TextElement,
        env: BuildEnvironment,
        symbol: Symbol,
    ) -> None:
        signode += addnodes.desc_sig_keyword('operator', 'operator')
        signode += addnodes.desc_sig_literal_string('""', '""')
        self.identifier.describe_signature(identnode, 'markType', env, '', '', symbol)


class ASTOperatorType(ASTOperator):
    """Represents a type conversion operator."""

    def __init__(self, type: ASTType) -> None:
        self.type = type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTOperatorType):
            return NotImplemented
        return self.type == other.type

    def __hash__(self) -> int:
        return hash(self.type)

    def get_id(self, version: int) -> str:
        if version == 1:
            return 'castto-%s-operator' % self.type.get_id(version)
        else:
            return 'cv' + self.type.get_id(version)

    def _stringify(self, transform: StringifyTransform) -> str:
        return f'operator {transform(self.type)}'

    def get_name_no_template(self) -> str:
        return str(self)

    def _describe_identifier(
        self,
        signode: TextElement,
        identnode: TextElement,
        env: BuildEnvironment,
        symbol: Symbol,
    ) -> None:
        signode += addnodes.desc_sig_keyword('operator', 'operator')
        signode += addnodes.desc_sig_space()
        self.type.describe_signature(identnode, 'markType', env, symbol)


class ASTTemplateArgConstant(ASTBase):
    """Represents a template argument that is a constant expression."""

    def __init__(self, value: ASTExpression) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateArgConstant):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def _stringify(self, transform: StringifyTransform) -> str:
        return transform(self.value)


# Define __all__ for this module
__all__ = [
    'ASTOperator',
    'ASTOperatorBuildIn',
    'ASTOperatorLiteral',
    'ASTOperatorType',
    'ASTTemplateArgConstant',
]
