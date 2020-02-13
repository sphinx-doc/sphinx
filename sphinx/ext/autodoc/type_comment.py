"""
    sphinx.ext.autodoc.type_comment
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Update annotations info of living objects using type_comments.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import ast
import itertools
from inspect import getsource
from typing import Any, Dict
from typing import cast

import sphinx
from sphinx.application import Sphinx
from sphinx.pycode.ast import parse as ast_parse
from sphinx.pycode.ast import unparse as ast_unparse
from sphinx.util import inspect
from sphinx.util import logging

logger = logging.getLogger(__name__)


def get_type_comment(obj: Any) -> Dict[str, Any]:
    """Get type_comment'ed FunctionDef object from living object.

    This tries to parse original code for living object and returns
    parameter dictionary for given *obj*.  It requires py38+ or typed_ast module.
    """
    try:
        source = getsource(obj)
        if source.startswith((' ', r'\t')):
            # subject is placed inside class or block.  To read its docstring,
            # this adds if-block before the declaration.
            module = ast_parse('if True:\n' + source)
            subject = cast(ast.FunctionDef, module.body[0].body[0])  # type: ignore
        else:
            module = ast_parse(source)
            subject = cast(ast.FunctionDef, module.body[0])  # type: ignore

        if getattr(subject, "type_comment", None):
            comment = subject.type_comment  # type: ignore
            if not comment.startswith("(...)"):
                node = cast(
                    ast.FunctionDef,
                    ast_parse(comment, mode='func_type')
                )
                results = {
                    'returns': node.returns,
                    'explicit': False,
                    'args': node.argtypes  # type: ignore
                }
            else:
                node = subject
                results = {
                    'returns': node.returns,
                    'explicit': True,
                    'args': {
                        arg.arg: arg.type_comment
                        for arg in itertools.chain(
                            getattr(node.args, "posonlyargs", []) or [],
                            getattr(node.args, "args", []) or [],
                            getattr(node.args, "vararg", []) or [],
                            getattr(node.args, "kwonlyargs", []) or [],
                            getattr(node.args, "kwarg", []) or [],
                        )
                    }
                }
            return results
        else:
            return None
    except (OSError, TypeError):  # failed to load source code
        return None
    except SyntaxError:  # failed to parse type_comments
        return None


def update_annotations_using_type_comments(app: Sphinx, obj: Any, bound_method: bool) -> None:
    """Update annotations info of *obj* using type_comments."""
    try:
        function = get_type_comment(obj)
        if function:
            explicit = function['explicit']
            args = function['args']
            sig = inspect.signature(obj, bound_method)
            for i, param in enumerate(sig.parameters.values()):
                if param.name not in obj.__annotations__:
                    type_hint = args[param.name if explicit else i]
                    annotation = ast_unparse(type_hint)
                    obj.__annotations__[param.name] = annotation

            if 'return' not in obj.__annotations__:
                obj.__annotations__['return'] = ast_unparse(function['returns'])
    except NotImplementedError as exc:  # failed to ast.unparse()
        logger.warning("Failed to parse type_comment for %r: %s", obj, exc)


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect('autodoc-before-process-signature', update_annotations_using_type_comments)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
