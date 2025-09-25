from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

    from sphinx.domains.cpp.ast_base import ASTBase

# Forward references to avoid circular imports
if TYPE_CHECKING:
    ASTTemplateParams = ASTBase
    ASTTemplateParamType = ASTBase
    ASTTemplateParamNonType = ASTBase
    ASTTemplateParamTemplateType = ASTBase
    ASTTemplateParamConstrainedTypeWithInit = ASTBase
    ASTTemplateIntroduction = ASTBase
    ASTTemplateIntroductionParameter = ASTBase
    ASTTemplateKeyParamPackIdDefault = ASTBase

# Import ASTBase for use in this module
from sphinx.domains.cpp.ast_base import ASTBase

# Placeholder classes for AST templates - these would need to be implemented
# based on the original AST file structure

class ASTTemplateDeclarationPrefix(ASTBase):
    """Represents a template declaration prefix."""

    def __init__(self, templates: list[Any]) -> None:
        self.templates = templates

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateDeclarationPrefix):
            return NotImplemented
        return self.templates == other.templates

    def __hash__(self) -> int:
        return hash(tuple(self.templates))


class ASTTemplateParams(ASTBase):
    """Represents template parameters."""

    def __init__(self, params: list[Any], requires_clause: Any) -> None:
        self.params = params
        self.requires_clause = requires_clause

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateParams):
            return NotImplemented
        return self.params == other.params and self.requires_clause == other.requires_clause

    def __hash__(self) -> int:
        return hash((tuple(self.params), self.requires_clause))


class ASTTemplateParamType(ASTBase):
    """Represents a type template parameter."""

    def __init__(self, data: Any) -> None:
        self.data = data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateParamType):
            return NotImplemented
        return self.data == other.data

    def __hash__(self) -> int:
        return hash(self.data)


class ASTTemplateParamNonType(ASTBase):
    """Represents a non-type template parameter."""

    def __init__(self, param: Any, parameter_pack: bool) -> None:
        self.param = param
        self.parameter_pack = parameter_pack

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateParamNonType):
            return NotImplemented
        return self.param == other.param and self.parameter_pack == other.parameter_pack

    def __hash__(self) -> int:
        return hash((self.param, self.parameter_pack))


class ASTTemplateParamTemplateType(ASTBase):
    """Represents a template template parameter."""

    def __init__(self, nested_params: Any, data: Any) -> None:
        self.nested_params = nested_params
        self.data = data

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateParamTemplateType):
            return NotImplemented
        return self.nested_params == other.nested_params and self.data == other.data

    def __hash__(self) -> int:
        return hash((self.nested_params, self.data))


class ASTTemplateParamConstrainedTypeWithInit(ASTBase):
    """Represents a constrained template parameter with initialization."""

    def __init__(self, type: Any, type_init: Any) -> None:
        self.type = type
        self.type_init = type_init

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateParamConstrainedTypeWithInit):
            return NotImplemented
        return self.type == other.type and self.type_init == other.type_init

    def __hash__(self) -> int:
        return hash((self.type, self.type_init))


class ASTTemplateIntroduction(ASTBase):
    """Represents a template introduction (requires clauses)."""

    def __init__(self, concept: Any, params: list[Any]) -> None:
        self.concept = concept
        self.params = params

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateIntroduction):
            return NotImplemented
        return self.concept == other.concept and self.params == other.params

    def __hash__(self) -> int:
        return hash((self.concept, tuple(self.params)))


class ASTTemplateIntroductionParameter(ASTBase):
    """Represents a parameter in a template introduction."""

    def __init__(self, identifier: Any, parameter_pack: bool) -> None:
        self.identifier = identifier
        self.parameter_pack = parameter_pack

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateIntroductionParameter):
            return NotImplemented
        return self.identifier == other.identifier and self.parameter_pack == other.parameter_pack

    def __hash__(self) -> int:
        return hash((self.identifier, self.parameter_pack))


class ASTTemplateKeyParamPackIdDefault(ASTBase):
    """Represents a template parameter with key, pack, id, and default."""

    def __init__(self, key: str, identifier: Any, parameter_pack: bool, default: Any) -> None:
        self.key = key
        self.identifier = identifier
        self.parameter_pack = parameter_pack
        self.default = default

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ASTTemplateKeyParamPackIdDefault):
            return NotImplemented
        return (
            self.key == other.key
            and self.identifier == other.identifier
            and self.parameter_pack == other.parameter_pack
            and self.default == other.default
        )

    def __hash__(self) -> int:
        return hash((self.key, self.identifier, self.parameter_pack, self.default))


class ASTTemplateParam(ASTBase):
    """Represents a template parameter."""

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self))

    def __hash__(self) -> int:
        return hash(type(self))


# Define __all__ for this module
__all__ = [
    'ASTTemplateDeclarationPrefix',
    'ASTTemplateParams',
    'ASTTemplateParam',
    'ASTTemplateParamType',
    'ASTTemplateParamNonType',
    'ASTTemplateParamTemplateType',
    'ASTTemplateParamConstrainedTypeWithInit',
    'ASTTemplateIntroduction',
    'ASTTemplateIntroductionParameter',
    'ASTTemplateKeyParamPackIdDefault',
]
