from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from sphinx.domains.cpp._ast import (
        ASTTemplateArgConstant,
        ASTTemplateArgs,
        ASTTemplateDeclarationPrefix,
        ASTTemplateIntroduction,
        ASTTemplateIntroductionParameter,
        ASTTemplateKeyParamPackIdDefault,
        ASTTemplateParamConstrainedTypeWithInit,
        ASTTemplateParamNonType,
        ASTTemplateParams,
        ASTTemplateParamTemplateType,
        ASTTemplateParamType,
    )
    from sphinx.domains.cpp.parser_base import BaseParser


class TemplateParser:
    """Mixin class containing template parsing methods for C++ parser."""

    def _parse_template_argument_list(self, parser: BaseParser) -> 'ASTTemplateArgs':
        """Parse template argument list."""
        # ... implementation would be here
        return None

    def _parse_template_parameter(self, parser: BaseParser) -> Any:
        """Parse a template parameter."""
        # ... implementation would be here
        return None

    def _parse_template_parameters(self, parser: BaseParser) -> 'ASTTemplateParams':
        """Parse template parameters."""
        # ... implementation would be here
        return None

    def _parse_template_declaration_prefix(
        self, parser: BaseParser
    ) -> 'ASTTemplateDeclarationPrefix':
        """Parse template declaration prefix."""
        # ... implementation would be here
        return None

    def _parse_template_introduction(
        self, parser: BaseParser
    ) -> 'ASTTemplateIntroduction':
        """Parse template introduction (requires clauses)."""
        # ... implementation would be here
        return None

    def _parse_requires_clause(self, parser: BaseParser) -> 'ASTRequiresClause':
        """Parse requires clause."""
        # ... implementation would be here
        return None

    def _parse_concept_definition(self, parser: BaseParser) -> 'ASTConcept':
        """Parse concept definition."""
        # ... implementation would be here
        return None

    def _parse_constrained_type_template_parameter(
        self, parser: BaseParser
    ) -> 'ASTTemplateParamConstrainedTypeWithInit':
        """Parse constrained type template parameter."""
        # ... implementation would be here
        return None

    def _parse_non_type_template_parameter(
        self, parser: BaseParser
    ) -> 'ASTTemplateParamNonType':
        """Parse non-type template parameter."""
        # ... implementation would be here
        return None

    def _parse_template_template_parameter(
        self, parser: BaseParser
    ) -> 'ASTTemplateParamTemplateType':
        """Parse template template parameter."""
        # ... implementation would be here
        return None

    def _parse_template_parameter_list(
        self, parser: BaseParser
    ) -> 'ASTTemplateParams':
        """Parse template parameter list."""
        # ... implementation would be here
        return None


# Define __all__ for this module
__all__ = ['TemplateParser']
