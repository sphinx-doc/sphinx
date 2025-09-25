from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.util.cfamily import ASTBaseParenExprList

if TYPE_CHECKING:
    from sphinx.util.cfamily import StringifyTransform

# Import ASTBase for use in this module
from sphinx.domains.cpp.ast_base import ASTBase


class ASTExpression(ASTBase):
    """Base class for all expressions."""

    def get_id(self, version: int) -> str:
        raise NotImplementedError


class ASTAlignofExpr(ASTExpression):
    """Represents an alignof expression."""

    def __init__(self, typ: Any) -> None:
        self.typ = typ

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTAlignofExpr):
            return NotImplemented
        return self.typ == other.typ

    def __hash__(self) -> int:
        return hash(self.typ)


class ASTSizeofExpr(ASTExpression):
    """Represents a sizeof expression."""

    def __init__(self, expr: ASTExpression) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTSizeofExpr):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


class ASTSizeofType(ASTExpression):
    """Represents a sizeof(type) expression."""

    def __init__(self, typ: Any) -> None:
        self.typ = typ

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTSizeofType):
            return NotImplemented
        return self.typ == other.typ

    def __hash__(self) -> int:
        return hash(self.typ)


class ASTSizeofParamPack(ASTExpression):
    """Represents a sizeof...(param) expression."""

    def __init__(self, identifier: Any) -> None:
        self.identifier = identifier

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTSizeofParamPack):
            return NotImplemented
        return self.identifier == other.identifier

    def __hash__(self) -> int:
        return hash(self.identifier)


class ASTCastExpr(ASTExpression):
    """Represents a cast expression."""

    def __init__(self, typ: Any, expr: ASTExpression) -> None:
        self.typ = typ
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTCastExpr):
            return NotImplemented
        return self.typ == other.typ and self.expr == other.expr

    def __hash__(self) -> int:
        return hash((self.typ, self.expr))


class ASTBinOpExpr(ASTExpression):
    """Represents a binary operation expression."""

    def __init__(self, exprs: list[ASTExpression], ops: list[str]) -> None:
        self.exprs = exprs
        self.ops = ops

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTBinOpExpr):
            return NotImplemented
        return self.exprs == other.exprs and self.ops == other.ops

    def __hash__(self) -> int:
        return hash((tuple(self.exprs), tuple(self.ops)))


class ASTConditionalExpr(ASTExpression):
    """Represents a conditional expression (ternary operator)."""

    def __init__(self, condition: ASTExpression, then_expr: ASTExpression, else_expr: ASTExpression) -> None:
        self.condition = condition
        self.then_expr = then_expr
        self.else_expr = else_expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTConditionalExpr):
            return NotImplemented
        return (
            self.condition == other.condition
            and self.then_expr == other.then_expr
            and self.else_expr == other.else_expr
        )

    def __hash__(self) -> int:
        return hash((self.condition, self.then_expr, self.else_expr))


class ASTCommaExpr(ASTExpression):
    """Represents a comma expression."""

    def __init__(self, exprs: list[ASTExpression]) -> None:
        self.exprs = exprs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTCommaExpr):
            return NotImplemented
        return self.exprs == other.exprs

    def __hash__(self) -> int:
        return hash(tuple(self.exprs))


class ASTAssignmentExpr(ASTExpression):
    """Represents an assignment expression."""

    def __init__(self, left_expr: ASTExpression, op: str, right_expr: ASTExpression) -> None:
        self.left_expr = left_expr
        self.op = op
        self.right_expr = right_expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTAssignmentExpr):
            return NotImplemented
        return (
            self.left_expr == other.left_expr
            and self.op == other.op
            and self.right_expr == other.right_expr
        )

    def __hash__(self) -> int:
        return hash((self.left_expr, self.op, self.right_expr))


class ASTBracedInitList(ASTExpression):
    """Represents a braced initialization list."""

    def __init__(self, exprs: list[Any], trailing_comma: bool) -> None:
        self.exprs = exprs
        self.trailing_comma = trailing_comma

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTBracedInitList):
            return NotImplemented
        return self.exprs == other.exprs and self.trailing_comma == other.trailing_comma

    def __hash__(self) -> int:
        return hash((tuple(self.exprs), self.trailing_comma))


class ASTUnaryOpExpr(ASTExpression):
    """Represents a unary operation expression."""

    def __init__(self, op: str, expr: ASTExpression) -> None:
        self.op = op
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTUnaryOpExpr):
            return NotImplemented
        return self.op == other.op and self.expr == other.expr

    def __hash__(self) -> int:
        return hash((self.op, self.expr))


class ASTNewExpr(ASTExpression):
    """Represents a new expression."""

    def __init__(self, rooted: bool, is_new_type_id: bool, type: Any, init_list: Any) -> None:
        self.rooted = rooted
        self.is_new_type_id = is_new_type_id
        self.type = type
        self.init_list = init_list

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNewExpr):
            return NotImplemented
        return (
            self.rooted == other.rooted
            and self.is_new_type_id == other.is_new_type_id
            and self.type == other.type
            and self.init_list == other.init_list
        )

    def __hash__(self) -> int:
        return hash((self.rooted, self.is_new_type_id, self.type, self.init_list))


class ASTDeleteExpr(ASTExpression):
    """Represents a delete expression."""

    def __init__(self, rooted: bool, array: bool, expr: ASTExpression) -> None:
        self.rooted = rooted
        self.array = array
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeleteExpr):
            return NotImplemented
        return (
            self.rooted == other.rooted
            and self.array == other.array
            and self.expr == other.expr
        )

    def __hash__(self) -> int:
        return hash((self.rooted, self.array, self.expr))


class ASTFallbackExpr(ASTExpression):
    """Represents a fallback expression for unparseable code."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTFallbackExpr):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)


class ASTPostfixExpr(ASTExpression):
    """Represents a postfix expression."""

    def __init__(self, prefix: Any, post_fixes: list[Any]) -> None:
        self.prefix = prefix
        self.post_fixes = post_fixes

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPostfixExpr):
            return NotImplemented
        return self.prefix == other.prefix and self.post_fixes == other.post_fixes

    def __hash__(self) -> int:
        return hash((self.prefix, tuple(self.post_fixes)))


class ASTPostfixOp(ASTBase):
    """Base class for postfix operators."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self))

    def __hash__(self) -> int:
        return hash(type(self))


class ASTPostfixArray(ASTPostfixOp):
    """Represents array access postfix operator."""

    def __init__(self, expr: ASTExpression) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPostfixArray):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


class ASTPostfixMember(ASTPostfixOp):
    """Represents member access postfix operator."""

    def __init__(self, name: ASTNestedName) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPostfixMember):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class ASTPostfixMemberOfPointer(ASTPostfixOp):
    """Represents pointer-to-member access postfix operator."""

    def __init__(self, name: ASTNestedName) -> None:
        self.name = name

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPostfixMemberOfPointer):
            return NotImplemented
        return self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)


class ASTPostfixInc(ASTPostfixOp):
    """Represents postfix increment operator."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ASTPostfixInc)

    def __hash__(self) -> int:
        return hash('++')


class ASTPostfixDec(ASTPostfixOp):
    """Represents postfix decrement operator."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ASTPostfixDec)

    def __hash__(self) -> int:
        return hash('--')


class ASTPostfixCallExpr(ASTPostfixOp):
    """Represents function call postfix operator."""

    def __init__(self, lst: Any) -> None:
        self.lst = lst

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPostfixCallExpr):
            return NotImplemented
        return self.lst == other.lst

    def __hash__(self) -> int:
        return hash(self.lst)


class ASTExplicitCast(ASTExpression):
    """Represents an explicit cast expression."""

    def __init__(self, cast: str, typ: Any, expr: ASTExpression) -> None:
        self.cast = cast
        self.typ = typ
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTExplicitCast):
            return NotImplemented
        return self.cast == other.cast and self.typ == other.typ and self.expr == other.expr

    def __hash__(self) -> int:
        return hash((self.cast, self.typ, self.expr))


class ASTTypeId(ASTExpression):
    """Represents a typeid expression."""

    def __init__(self, type_or_expr: Any, is_type: bool) -> None:
        self.type_or_expr = type_or_expr
        self.is_type = is_type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTypeId):
            return NotImplemented
        return self.type_or_expr == other.type_or_expr and self.is_type == other.is_type

    def __hash__(self) -> int:
        return hash((self.type_or_expr, self.is_type))


class ASTNoexceptExpr(ASTExpression):
    """Represents a noexcept expression."""

    def __init__(self, expr: ASTExpression) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNoexceptExpr):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


class ASTFoldExpr(ASTExpression):
    """Represents a fold expression."""

    def __init__(self, left: ASTExpression | None, op: str, right: ASTExpression) -> None:
        self.left = left
        self.op = op
        self.right = right

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTFoldExpr):
            return NotImplemented
        return self.left == other.left and self.op == other.op and self.right == other.right

    def __hash__(self) -> int:
        return hash((self.left, self.op, self.right))


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
    'ASTAlignofExpr',
    'ASTSizeofExpr',
    'ASTSizeofType',
    'ASTSizeofParamPack',
    'ASTCastExpr',
    'ASTBinOpExpr',
    'ASTConditionalExpr',
    'ASTCommaExpr',
    'ASTAssignmentExpr',
    'ASTBracedInitList',
    'ASTUnaryOpExpr',
    'ASTNewExpr',
    'ASTDeleteExpr',
    'ASTFallbackExpr',
    'ASTPostfixExpr',
    'ASTPostfixOp',
    'ASTPostfixArray',
    'ASTPostfixMember',
    'ASTPostfixMemberOfPointer',
    'ASTPostfixInc',
    'ASTPostfixDec',
    'ASTPostfixCallExpr',
    'ASTExplicitCast',
    'ASTTypeId',
    'ASTNoexceptExpr',
]
