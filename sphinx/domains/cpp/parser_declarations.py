from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from sphinx.domains.cpp._ast import (
        ASTBaseClass,
        ASTDeclaration,
        ASTDeclarator,
        ASTDeclSpecs,
        ASTDeclSpecsSimple,
        ASTEnum,
        ASTFunctionParameter,
        ASTInitializer,
        ASTParametersQualifiers,
        ASTTemplateDeclarationPrefix,
    )
    from sphinx.domains.cpp.parser_base import BaseParser


class DeclarationParser:
    """Mixin class containing declaration parsing methods for C++ parser."""

    def _parse_decl_specs_simple(
        self, parser: BaseParser, outer: str, typed: bool
    ) -> 'ASTDeclSpecsSimple':
        """Parse simple declaration specifiers."""
        # ... implementation would be here
        return None

    def _parse_decl_specs(self, parser: BaseParser, outer: str, typed: bool = True) -> 'ASTDeclSpecs':
        """Parse declaration specifiers."""
        # ... implementation would be here
        return None

    def _parse_declarator_name_suffix(self, parser: BaseParser) -> None:
        """Parse declarator name suffix (for bitfields, etc.)."""
        # ... implementation would be here
        pass

    def _parse_declarator(self, parser: BaseParser) -> 'ASTDeclarator':
        """Parse a declarator."""
        # ... implementation would be here
        return None

    def _parse_initializer(self, parser: BaseParser) -> 'ASTInitializer':
        """Parse an initializer."""
        # ... implementation would be here
        return None

    def _parse_function_parameter(self, parser: BaseParser) -> 'ASTFunctionParameter':
        """Parse a function parameter."""
        # ... implementation would be here
        return None

    def _parse_parameters_and_qualifiers(
        self, parser: BaseParser
    ) -> 'ASTParametersQualifiers':
        """Parse function parameters and qualifiers."""
        # ... implementation would be here
        return None

    def _parse_base_class(self, parser: BaseParser) -> 'ASTBaseClass':
        """Parse a base class specification."""
        # ... implementation would be here
        return None

    def _parse_enum(self, parser: BaseParser) -> 'ASTEnum':
        """Parse an enum definition."""
        # ... implementation would be here
        return None

    def _parse_concept(self, parser: BaseParser) -> 'ASTConcept':
        """Parse a concept definition."""
        # ... implementation would be here
        return None

    def _parse_namespace(self, parser: BaseParser) -> 'ASTNamespace':
        """Parse a namespace definition."""
        # ... implementation would be here
        return None

    def _parse_declaration(self, parser: BaseParser) -> 'ASTDeclaration':
        """Parse a declaration."""
        # ... implementation would be here
        return None


# Define __all__ for this module
__all__ = ['DeclarationParser']
