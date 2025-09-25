from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from sphinx.domains.cpp.ast_base import ASTBase

# Forward references to avoid circular imports
if TYPE_CHECKING:
    ASTDeclSpecs = ASTBase
    ASTDeclarator = ASTBase
    ASTInitializer = ASTBase

# Import ASTBase for use in this module
from sphinx.domains.cpp.ast_base import ASTBase

# Placeholder classes for AST declarations - these would need to be implemented
# based on the original AST file structure

class ASTDeclaration(ASTBase):
    """Represents a C++ declaration."""

    def __init__(
        self,
        object_type: str,
        directive_type: str,
        visibility: str | None,
        template_prefix: Any,
        declaration: Any,
        trailing_requires_clause: Any,
        semicolon: bool,
    ) -> None:
        self.object_type = object_type
        self.directive_type = directive_type
        self.visibility = visibility
        self.template_prefix = template_prefix
        self.declaration = declaration
        self.trailing_requires_clause = trailing_requires_clause
        self.semicolon = semicolon

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaration):
            return NotImplemented
        return (
            self.object_type == other.object_type
            and self.directive_type == other.directive_type
            and self.visibility == other.visibility
            and self.template_prefix == other.template_prefix
            and self.declaration == other.declaration
            and self.trailing_requires_clause == other.trailing_requires_clause
            and self.semicolon == other.semicolon
        )

    def __hash__(self) -> int:
        return hash((
            self.object_type,
            self.directive_type,
            self.visibility,
            self.template_prefix,
            self.declaration,
            self.trailing_requires_clause,
            self.semicolon,
        ))


class ASTDeclSpecs(ASTBase):
    """Represents declaration specifiers."""

    def __init__(self, outer: str, left_specs: Any, right_specs: Any, trailing: Any) -> None:
        self.outer = outer
        self.left_specs = left_specs
        self.right_specs = right_specs
        self.trailing = trailing

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclSpecs):
            return NotImplemented
        return (
            self.outer == other.outer
            and self.left_specs == other.left_specs
            and self.right_specs == other.right_specs
            and self.trailing == other.trailing
        )

    def __hash__(self) -> int:
        return hash((self.outer, self.left_specs, self.right_specs, self.trailing))


class ASTDeclSpecsSimple(ASTBase):
    """Represents simple declaration specifiers."""

    def __init__(
        self,
        storage: str | None,
        thread_local: str | None,
        inline: str | None,
        virtual: str | None,
        explicit_spec: Any,
        consteval: str | None,
        constexpr: str | None,
        constinit: str | None,
        volatile: str | None,
        const: str | None,
        friend: str | None,
        attrs: Any,
    ) -> None:
        self.storage = storage
        self.thread_local = thread_local
        self.inline = inline
        self.virtual = virtual
        self.explicit_spec = explicit_spec
        self.consteval = consteval
        self.constexpr = constexpr
        self.constinit = constinit
        self.volatile = volatile
        self.const = const
        self.friend = friend
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclSpecsSimple):
            return NotImplemented
        return (
            self.storage == other.storage
            and self.thread_local == other.thread_local
            and self.inline == other.inline
            and self.virtual == other.virtual
            and self.explicit_spec == other.explicit_spec
            and self.consteval == other.consteval
            and self.constexpr == other.constexpr
            and self.constinit == other.constinit
            and self.volatile == other.volatile
            and self.const == other.const
            and self.friend == other.friend
            and self.attrs == other.attrs
        )

    def __hash__(self) -> int:
        return hash((
            self.storage,
            self.thread_local,
            self.inline,
            self.virtual,
            self.explicit_spec,
            self.consteval,
            self.constexpr,
            self.constinit,
            self.volatile,
            self.const,
            self.friend,
            self.attrs,
        ))


class ASTBaseClass(ASTBase):
    """Represents a base class in class inheritance."""

    def __init__(self, name: Any, visibility: str | None, virtual: bool, pack: bool) -> None:
        self.name = name
        self.visibility = visibility
        self.virtual = virtual
        self.pack = pack

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTBaseClass):
            return NotImplemented
        return (
            self.name == other.name
            and self.visibility == other.visibility
            and self.virtual == other.virtual
            and self.pack == other.pack
        )

    def __hash__(self) -> int:
        return hash((self.name, self.visibility, self.virtual, self.pack))


class ASTClass(ASTBase):
    """Represents a class declaration."""

    def __init__(self, name: Any, final: bool, bases: list[ASTBaseClass], attrs: Any) -> None:
        self.name = name
        self.final = final
        self.bases = bases
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTClass):
            return NotImplemented
        return (
            self.name == other.name
            and self.final == other.final
            and self.bases == other.bases
            and self.attrs == other.attrs
        )

    def __hash__(self) -> int:
        return hash((self.name, self.final, tuple(self.bases), self.attrs))


class ASTUnion(ASTBase):
    """Represents a union declaration."""

    def __init__(self, name: Any, attrs: Any) -> None:
        self.name = name
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTUnion):
            return NotImplemented
        return self.name == other.name and self.attrs == other.attrs

    def __hash__(self) -> int:
        return hash((self.name, self.attrs))


class ASTEnum(ASTBase):
    """Represents an enum declaration."""

    def __init__(self, name: Any, scoped: str | None, underlying_type: Any, attrs: Any) -> None:
        self.name = name
        self.scoped = scoped
        self.underlying_type = underlying_type
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTEnum):
            return NotImplemented
        return (
            self.name == other.name
            and self.scoped == other.scoped
            and self.underlying_type == other.underlying_type
            and self.attrs == other.attrs
        )

    def __hash__(self) -> int:
        return hash((self.name, self.scoped, self.underlying_type, self.attrs))


class ASTEnumerator(ASTBase):
    """Represents an enumerator in an enum."""

    def __init__(self, name: Any, init: Any, attrs: Any) -> None:
        self.name = name
        self.init = init
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTEnumerator):
            return NotImplemented
        return self.name == other.name and self.init == other.init and self.attrs == other.attrs

    def __hash__(self) -> int:
        return hash((self.name, self.init, self.attrs))


class ASTConcept(ASTBase):
    """Represents a concept definition."""

    def __init__(self, nested_name: Any, initializer: Any) -> None:
        self.nested_name = nested_name
        self.initializer = initializer

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTConcept):
            return NotImplemented
        return self.nested_name == other.nested_name and self.initializer == other.initializer

    def __hash__(self) -> int:
        return hash((self.nested_name, self.initializer))


class ASTNamespace(ASTBase):
    """Represents a namespace."""

    def __init__(self, nested_name: Any, template_prefix: Any) -> None:
        self.nested_name = nested_name
        self.template_prefix = template_prefix

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNamespace):
            return NotImplemented
        return self.nested_name == other.nested_name and self.template_prefix == other.template_prefix

    def __hash__(self) -> int:
        return hash((self.nested_name, self.template_prefix))


class ASTDeclarator(ASTBase):
    """Base class for declarators."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self))

    def __hash__(self) -> int:
        return hash(type(self))


class ASTDeclaratorPtr(ASTDeclarator):
    """Represents a pointer declarator."""

    def __init__(self, next: ASTDeclarator, volatile: bool, const: bool, attrs: Any) -> None:
        self.next = next
        self.volatile = volatile
        self.const = const
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorPtr):
            return NotImplemented
        return (
            self.next == other.next
            and self.volatile == other.volatile
            and self.const == other.const
            and self.attrs == other.attrs
        )

    def __hash__(self) -> int:
        return hash((self.next, self.volatile, self.const, self.attrs))


class ASTDeclaratorRef(ASTDeclarator):
    """Represents a reference declarator."""

    def __init__(self, next: ASTDeclarator, attrs: Any) -> None:
        self.next = next
        self.attrs = attrs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorRef):
            return NotImplemented
        return self.next == other.next and self.attrs == other.attrs

    def __hash__(self) -> int:
        return hash((self.next, self.attrs))


class ASTDeclaratorMemPtr(ASTDeclarator):
    """Represents a pointer-to-member declarator."""

    def __init__(self, name: Any, const: bool, volatile: bool, next: ASTDeclarator) -> None:
        self.name = name
        self.const = const
        self.volatile = volatile
        self.next = next

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorMemPtr):
            return NotImplemented
        return (
            self.name == other.name
            and self.const == other.const
            and self.volatile == other.volatile
            and self.next == other.next
        )

    def __hash__(self) -> int:
        return hash((self.name, self.const, self.volatile, self.next))


class ASTDeclaratorParen(ASTDeclarator):
    """Represents a parenthesized declarator."""

    def __init__(self, inner: ASTDeclarator, next: ASTDeclarator) -> None:
        self.inner = inner
        self.next = next

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorParen):
            return NotImplemented
        return self.inner == other.inner and self.next == other.next

    def __hash__(self) -> int:
        return hash((self.inner, self.next))


class ASTDeclaratorNameParamQual(ASTDeclarator):
    """Represents a declarator with name, parameters, and qualifiers."""

    def __init__(self, decl_id: Any, array_ops: list[Any], param_qual: Any) -> None:
        self.decl_id = decl_id
        self.array_ops = array_ops
        self.param_qual = param_qual

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorNameParamQual):
            return NotImplemented
        return (
            self.decl_id == other.decl_id
            and self.array_ops == other.array_ops
            and self.param_qual == other.param_qual
        )

    def __hash__(self) -> int:
        return hash((self.decl_id, tuple(self.array_ops), self.param_qual))


class ASTDeclaratorNameBitField(ASTDeclarator):
    """Represents a bit-field declarator."""

    def __init__(self, decl_id: Any, size: Any) -> None:
        self.decl_id = decl_id
        self.size = size

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorNameBitField):
            return NotImplemented
        return self.decl_id == other.decl_id and self.size == other.size

    def __hash__(self) -> int:
        return hash((self.decl_id, self.size))


class ASTDeclaratorParamPack(ASTDeclarator):
    """Represents a parameter pack declarator."""

    def __init__(self, next: ASTDeclarator) -> None:
        self.next = next

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTDeclaratorParamPack):
            return NotImplemented
        return self.next == other.next

    def __hash__(self) -> int:
        return hash(self.next)


class ASTInitializer(ASTBase):
    """Represents an initializer."""

    def __init__(self, value: Any, has_assign: bool = True) -> None:
        self.value = value
        self.has_assign = has_assign

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTInitializer):
            return NotImplemented
        return self.value == other.value and self.has_assign == other.has_assign

    def __hash__(self) -> int:
        return hash((self.value, self.has_assign))


class ASTFunctionParameter(ASTBase):
    """Represents a function parameter."""

    def __init__(self, arg: Any, variadic: bool = False) -> None:
        self.arg = arg
        self.variadic = variadic

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTFunctionParameter):
            return NotImplemented
        return self.arg == other.arg and self.variadic == other.variadic

    def __hash__(self) -> int:
        return hash((self.arg, self.variadic))


class ASTParametersQualifiers(ASTBase):
    """Represents function parameters and qualifiers."""

    def __init__(
        self,
        args: list[ASTFunctionParameter],
        volatile: bool,
        const: bool,
        ref_qual: str | None,
        exception_spec: Any,
        trailing_return: Any,
        override: bool,
        final: bool,
        attrs: Any,
        initializer: str | None,
    ) -> None:
        self.args = args
        self.volatile = volatile
        self.const = const
        self.ref_qual = ref_qual
        self.exception_spec = exception_spec
        self.trailing_return = trailing_return
        self.override = override
        self.final = final
        self.attrs = attrs
        self.initializer = initializer

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTParametersQualifiers):
            return NotImplemented
        return (
            self.args == other.args
            and self.volatile == other.volatile
            and self.const == other.const
            and self.ref_qual == other.ref_qual
            and self.exception_spec == other.exception_spec
            and self.trailing_return == other.trailing_return
            and self.override == other.override
            and self.final == other.final
            and self.attrs == other.attrs
            and self.initializer == other.initializer
        )

    def __hash__(self) -> int:
        return hash((
            tuple(self.args),
            self.volatile,
            self.const,
            self.ref_qual,
            self.exception_spec,
            self.trailing_return,
            self.override,
            self.final,
            self.attrs,
            self.initializer,
        ))


class ASTParenExprList(ASTBase):
    """Represents a parenthesized expression list."""

    def __init__(self, exprs: list[Any]) -> None:
        self.exprs = exprs

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTParenExprList):
            return NotImplemented
        return self.exprs == other.exprs

    def __hash__(self) -> int:
        return hash(tuple(self.exprs))


class ASTExplicitSpec(ASTBase):
    """Represents an explicit specifier."""

    def __init__(self, expr: Any) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTExplicitSpec):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


class ASTNoexceptSpec(ASTBase):
    """Represents a noexcept specifier."""

    def __init__(self, expr: Any) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTNoexceptSpec):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


class ASTRequiresClause(ASTBase):
    """Represents a requires clause."""

    def __init__(self, expr: Any) -> None:
        self.expr = expr

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTRequiresClause):
            return NotImplemented
        return self.expr == other.expr

    def __hash__(self) -> int:
        return hash(self.expr)


# Define __all__ for this module
__all__ = [
    'ASTDeclaration',
    'ASTDeclSpecs',
    'ASTDeclSpecsSimple',
    'ASTBaseClass',
    'ASTClass',
    'ASTUnion',
    'ASTEnum',
    'ASTEnumerator',
    'ASTConcept',
    'ASTNamespace',
    'ASTDeclarator',
    'ASTDeclaratorPtr',
    'ASTDeclaratorRef',
    'ASTDeclaratorMemPtr',
    'ASTDeclaratorParen',
    'ASTDeclaratorNameParamQual',
    'ASTDeclaratorNameBitField',
    'ASTDeclaratorParamPack',
    'ASTInitializer',
    'ASTFunctionParameter',
    'ASTParametersQualifiers',
    'ASTParenExprList',
    'ASTExplicitSpec',
    'ASTNoexceptSpec',
    'ASTRequiresClause',
]
