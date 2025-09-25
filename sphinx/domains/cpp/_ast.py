from __future__ import annotations

# Re-export all AST classes for backward compatibility
# This module has been modularized - see the individual modules for details

from sphinx.domains.cpp.ast_base import *  # noqa: F403
from sphinx.domains.cpp.ast_names import *  # noqa: F403
from sphinx.domains.cpp.ast_expressions import *  # noqa: F403
from sphinx.domains.cpp.ast_operators import *  # noqa: F403
from sphinx.domains.cpp.ast_types import *  # noqa: F403
from sphinx.domains.cpp.ast_declarations import *  # noqa: F403
from sphinx.domains.cpp.ast_templates import *  # noqa: F403

# Define __all__ to explicitly export all classes
__all__ = [
    # Base classes
    'ASTBase',

    # Name classes
    'ASTIdentifier',
    'ASTNestedNameElement',
    'ASTNestedName',

    # Expression classes
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
    'ASTPostfixOp',
    'ASTPostfixArray',
    'ASTPostfixMember',
    'ASTPostfixMemberOfPointer',
    'ASTPostfixInc',
    'ASTPostfixDec',
    'ASTPostfixCallExpr',
    'ASTPostfixExpr',
    'ASTExplicitCast',
    'ASTTypeId',
    'ASTUnaryOpExpr',
    'ASTSizeofParamPack',
    'ASTSizeofType',
    'ASTSizeofExpr',
    'ASTAlignofExpr',
    'ASTNoexceptExpr',
    'ASTNewExpr',
    'ASTDeleteExpr',
    'ASTCastExpr',
    'ASTBinOpExpr',
    'ASTConditionalExpr',
    'ASTBracedInitList',
    'ASTAssignmentExpr',
    'ASTCommaExpr',
    'ASTFallbackExpr',

    # Operator classes
    'ASTOperator',
    'ASTOperatorBuildIn',
    'ASTOperatorLiteral',
    'ASTOperatorType',

    # Template classes
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

    # Declaration classes
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

    # Declarator classes
    'ASTDeclarator',
    'ASTDeclaratorPtr',
    'ASTDeclaratorRef',
    'ASTDeclaratorMemPtr',
    'ASTDeclaratorParen',
    'ASTDeclaratorNameParamQual',
    'ASTDeclaratorNameBitField',
    'ASTDeclaratorParamPack',

    # Template classes
    'ASTTemplateDeclarationPrefix',
    'ASTTemplateParams',
    'ASTTemplateParamType',
    'ASTTemplateParamNonType',
    'ASTTemplateParamTemplateType',
    'ASTTemplateParamConstrainedTypeWithInit',
    'ASTTemplateIntroduction',
    'ASTTemplateIntroductionParameter',
    'ASTTemplateKeyParamPackIdDefault',

    # Other classes
    'ASTInitializer',
    'ASTFunctionParameter',
    'ASTParametersQualifiers',
    'ASTParenExprList',
    'ASTExplicitSpec',
    'ASTNoexceptSpec',
    'ASTRequiresClause',
]
