from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from sphinx.util.cfamily import StringifyTransform

    from sphinx.domains.cpp.ast_base import ASTBase
    from sphinx.domains.cpp.ast_expressions import ASTExpression
    from sphinx.domains.cpp.ast_names import ASTNestedName
    from sphinx.domains.cpp.ast_declarations import ASTDeclSpecs, ASTDeclarator, ASTInitializer

# Import ASTBase for use in this module
from sphinx.domains.cpp.ast_base import ASTBase

# Forward references to avoid circular imports
if TYPE_CHECKING:
    ASTExpression = ASTBase
    ASTNestedName = ASTBase
    ASTDeclSpecs = ASTBase
    ASTDeclarator = ASTBase
    ASTInitializer = ASTBase

# Placeholder classes for AST types - these would need to be implemented
# based on the original AST file structure

class ASTTemplateArgConstant(ASTBase):
    """Represents a template argument that is a constant expression."""

    def __init__(self, value: Any) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateArgConstant):
            return NotImplemented
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)

    def _stringify(self, transform: StringifyTransform) -> str:
        return transform(self.value)


class ASTTemplateArgs(ASTBase):
    """Represents template arguments."""

    def __init__(self, args: list[ASTType | ASTTemplateArgConstant], pack_expansion: bool) -> None:
        self.args = args
        self.pack_expansion = pack_expansion

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateArgs):
            return NotImplemented
        return self.args == other.args and self.pack_expansion == other.pack_expansion

    def __hash__(self) -> int:
        return hash((tuple(self.args), self.pack_expansion))

    def get_id(self, version: int) -> str:
        # Implementation would be here
        return ''


class ASTTrailingTypeSpec(ASTBase):
    """Base class for trailing type specifiers."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self))

    def __hash__(self) -> int:
        return hash(type(self))


class ASTTrailingTypeSpecFundamental(ASTTrailingTypeSpec):
    """Represents fundamental type specifiers."""

    def __init__(self, names: list[str], canon_names: list[str]) -> None:
        self.names = names
        self.canon_names = canon_names

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTrailingTypeSpecFundamental):
            return NotImplemented
        return self.names == other.names and self.canon_names == other.canon_names

    def __hash__(self) -> int:
        return hash((tuple(self.names), tuple(self.canon_names)))


class ASTTrailingTypeSpecDecltypeAuto(ASTTrailingTypeSpec):
    """Represents decltype(auto)."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ASTTrailingTypeSpecDecltypeAuto)

    def __hash__(self) -> int:
        return hash('decltype(auto)')


class ASTTrailingTypeSpecDecltype(ASTTrailingTypeSpec):
    """Represents decltype(expr)."""

    def __init__(self, expr: ASTExpression) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTrailingTypeSpecDecltype):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


class ASTTrailingTypeSpecName(ASTTrailingTypeSpec):
    """Represents named type specifiers."""

    def __init__(self, prefix: str | None, nested_name: ASTNestedName, placeholder_type: str | None) -> None:
        self.prefix = prefix
        self.nested_name = nested_name
        self.placeholder_type = placeholder_type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTrailingTypeSpecName):
            return NotImplemented
        return (
            self.prefix == other.prefix
            and self.nested_name == other.nested_name
            and self.placeholder_type == other.placeholder_type
        )

    def __hash__(self) -> int:
        return hash((self.prefix, self.nested_name, self.placeholder_type))


class ASTType(ASTBase):
    """Represents a type in C++."""

    def __init__(self, decl_specs: ASTDeclSpecs, declarator: ASTDeclarator) -> None:
        self.decl_specs = decl_specs
        self.declarator = declarator

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTType):
            return NotImplemented
        return self.decl_specs == other.decl_specs and self.declarator == other.declarator

    def __hash__(self) -> int:
        return hash((self.decl_specs, self.declarator))

    def get_id(self, version: int) -> str:
        # Implementation would be here
        return ''


class ASTTypeUsing(ASTBase):
    """Represents a type alias."""

    def __init__(self, name: ASTNestedName, type: ASTType | None) -> None:
        self.name = name
        self.type = type

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTypeUsing):
            return NotImplemented
        return self.name == other.name and self.type == other.type

    def __hash__(self) -> int:
        return hash((self.name, self.type))


class ASTTypeWithInit(ASTBase):
    """Represents a type with initializer."""

    def __init__(self, type: ASTType, init: ASTInitializer | None) -> None:
        self.type = type
        self.init = init

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTypeWithInit):
            return NotImplemented
        return self.type == other.type and self.init == other.init

    def __hash__(self) -> int:
        return hash((self.type, self.init))


class ASTArray(ASTBase):
    """Represents an array type."""

    def __init__(self, size: ASTExpression | None) -> None:
        self.size = size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTArray):
            return NotImplemented
        return self.size == other.size

    def __hash__(self) -> int:
        return hash(self.size)


class ASTPackExpansionExpr(ASTBase):
    """Represents a pack expansion expression."""

    def __init__(self, expr: ASTExpression) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTPackExpansionExpr):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


# Define __all__ for this module
__all__ = [
    'ASTTemplateArgConstant',
    'ASTTemplateArgs',
    'ASTTrailingTypeSpec',
    'ASTTrailingTypeSpecFundamental',
    'ASTTrailingTypeSpecDecltypeAuto',
    'ASTTrailingTypeSpecDecltype',
    'ASTTrailingTypeSpecName',
    'ASTType',
    'ASTTypeUsing',
    'ASTTypeWithInit',
    'ASTArray',
    'ASTPackExpansionExpr',
]
