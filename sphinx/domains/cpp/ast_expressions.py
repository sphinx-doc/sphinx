from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.domains.cpp.ast_base import ASTBase
from sphinx.util.cfamily import ASTBaseParenExprList

if TYPE_CHECKING:
    from sphinx.util.cfamily import StringifyTransform


class ASTExpression(ASTBase):
    """Base class for all expressions."""

    def get_id(self, version: int) -> str:
        raise NotImplementedError


class ASTLiteral(ASTExpression):
    """Base class for literal expressions."""
    pass


class ASTPointerLiteral(ASTLiteral):
    """Represents a pointer literal (nullptr)."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPointerLiteral):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def get_id(self, version: int) -> str:
        if version == 1:
            return 'LDnE'
        else:
            return 'LDnE'

    def _stringify(self, transform: StringifyTransform) -> str:
        return self.value


class ASTBooleanLiteral(ASTLiteral):
    """Represents a boolean literal (true/false)."""

    def __init__(self, value: bool) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTBooleanLiteral):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def get_id(self, version: int) -> str:
        if self.value:
            return 'Lb1E' if version >= 2 else 'Li1E'
        else:
            return 'Lb0E' if version >= 2 else 'Li0E'

    def _stringify(self, transform: StringifyTransform) -> str:
        return 'true' if self.value else 'false'


class ASTNumberLiteral(ASTLiteral):
    """Represents a numeric literal."""

    def __init__(self, data: str) -> None:
        self.data = data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNumberLiteral):
            return NotImplemented
        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def get_id(self, version: int) -> str:
        return 'Li' + str(len(self.data)) + self.data + 'E'

    def _stringify(self, transform: StringifyTransform) -> str:
        return self.data


class ASTStringLiteral(ASTLiteral):
    """Represents a string literal."""

    def __init__(self, data: str) -> None:
        self.data = data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTStringLiteral):
            return NotImplemented
        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)

    def get_id(self, version: int) -> str:
        return 'L' + str(len(self.data)) + self.data + 'E'

    def _stringify(self, transform: StringifyTransform) -> str:
        return self.data


class ASTCharLiteral(ASTLiteral):
    """Represents a character literal."""

    def __init__(self, prefix: str, data: str) -> None:
        self.prefix = prefix
        self.data = data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTCharLiteral):
            return NotImplemented
        return self.prefix == other.prefix and self.data == other.data

    def __hash__(self) -> int:
        return hash((self.prefix, self.data))

    def get_id(self, version: int) -> str:
        return 'L' + str(len(self.data)) + self.data + 'E'

    def _stringify(self, transform: StringifyTransform) -> str:
        return self.prefix + self.data


class ASTUserDefinedLiteral(ASTLiteral):
    """Represents a user-defined literal."""

    def __init__(self, literal: ASTLiteral, ident: ASTIdentifier) -> None:
        self.literal = literal
        self.ident = ident

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTUserDefinedLiteral):
            return NotImplemented
        return self.literal == other.literal and self.ident == other.ident

    def __hash__(self) -> int:
        return hash((self.literal, self.ident))

    def get_id(self, version: int) -> str:
        return self.literal.get_id(version) + 'li' + self.ident.get_id(version)

    def _stringify(self, transform: StringifyTransform) -> str:
        return transform(self.literal) + transform(self.ident)


class ASTThisLiteral(ASTExpression):
    """Represents the 'this' literal."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ASTThisLiteral)

    def __hash__(self) -> int:
        return hash('this')

    def get_id(self, version: int) -> str:
        return 'fpT'

    def _stringify(self, transform: StringifyTransform) -> str:
        return 'this'


class ASTFoldExpr(ASTExpression):
    """Represents a fold expression."""

    def __init__(
        self,
        left: ASTExpression | None,
        op: str,
        right: ASTExpression,
        is_left_fold: bool,
    ) -> None:
        self.left = left
        self.op = op
        self.right = right
        self.is_left_fold = is_left_fold

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTFoldExpr):
            return NotImplemented
        return (
            self.left == other.left
            and self.op == other.op
            and self.right == other.right
            and self.is_left_fold == other.is_left_fold
        )

    def __hash__(self) -> int:
        return hash((self.left, self.op, self.right, self.is_left_fold))

    def get_id(self, version: int) -> str:
        res = []
        if self.is_left_fold:
            res.append('fl')
        else:
            res.append('fr')
        if self.left:
            res.append(self.left.get_id(version))
        res.append(self.op)
        res.append(self.right.get_id(version))
        return ''.join(res)

    def _stringify(self, transform: StringifyTransform) -> str:
        res = []
        if self.left:
            res.append(transform(self.left))
        res.append('...')
        res.append(self.op)
        res.append('...')
        if self.right:
            res.append(transform(self.right))
        return ' '.join(res)


class ASTParenExpr(ASTExpression):
    """Represents a parenthesized expression."""

    def __init__(self, expr: ASTExpression) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTParenExpr):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)

    def get_id(self, version: int) -> str:
        return self.expr.get_id(version)

    def _stringify(self, transform: StringifyTransform) -> str:
        return f'({transform(self.expr)})'


class ASTIdExpression(ASTExpression):
    """Represents an identifier expression."""

    def __init__(self, name: ASTNestedName) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTIdExpression):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def get_id(self, version: int) -> str:
        return self.name.get_id(version)

    def _stringify(self, transform: StringifyTransform) -> str:
        return transform(self.name)


# Define __all__ for this module
__all__ = [
    'ASTExpression',
    'ASTLiteral',
    'ASTPointerLiteral',
    'ASTBooleanLiteral',
    'ASTNumberLiteral',
    'ASTStringLiteral',
    'ASTCharLiteral',
    'ASTUserDefinedLiteral',
    'ASTThisLiteral',
    'ASTFoldExpr',
    'ASTParenExpr',
    'ASTIdExpression',
]
