"""
    sphinx.ext.autodoc.typehints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Update annotations info of living objects using type_comments.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import inspect
import sys
from typing import Any, Dict, Generator, Union

import sphinx
from sphinx.application import Sphinx

if sys.version_info > (3, 8):
    import ast
else:
    try:
        from typed_ast import ast3 as ast
    except ImportError:
        ast = None


def ast_parse(code: str, mode: str = 'exec') -> "ast.AST":
    """Parse the *code* using built-in ast or typed_ast."""
    try:
        return ast.parse(code, mode=mode, type_comments=True)  # type: ignore
    except TypeError:
        # fallback to typed_ast3
        return ast.parse(code, mode=mode)


def iter_args(func: Union[ast.FunctionDef, ast.AsyncFunctionDef]
              ) -> Generator[ast.arg, None, None]:
    """Get an iterator for arguments names from FunctionDef node."""
    if hasattr(func.args, "posonlyargs"):  # py38 or above
        yield from func.args.posonlyargs  # type: ignore
    yield from func.args.args
    if func.args.vararg:
        yield func.args.vararg
    if func.args.kwarg:
        yield func.args.kwarg


def get_type_hints_from_type_comment(obj: Any, bound_method: bool) -> Dict[str, str]:
    """Get type hints from type_comment style annotation."""
    def getvalue(typ: ast.AST) -> str:
        if isinstance(typ, ast.Name):
            return typ.id
        elif isinstance(typ, ast.Subscript):
            return "%s[%s]" % (getvalue(typ.value), getvalue(typ.slice))
        elif isinstance(typ, ast.Index):
            return getvalue(typ.value)
        elif isinstance(typ, ast.Tuple):
            return ', '.join(str(getvalue(e)) for e in typ.elts)
        elif isinstance(typ, (ast.Constant, ast.NameConstant)):  # type: ignore
            return repr(typ.value)
        else:
            raise NotImplementedError

    try:
        source = inspect.getsource(obj)
        if source.startswith((' ', r'\t')):
            # subject is placed inside class or block.  To read its docstring,
            # this adds if-block before the declaration.
            module = ast_parse('if True:\n' + source)
            subject = module.body[0].body[0]  # type: ignore
        else:
            module = ast_parse(source)
            subject = module.body[0]  # type: ignore

        if subject.type_comment is None:  # no type_comment
            return {}
        else:
            func = ast.parse(subject.type_comment, mode='func_type')  # type: Any

            type_hints = {}  # type: Dict[str, Any]
            type_hints['return'] = getvalue(func.returns)

            if func.argtypes != [ast.Ellipsis]:
                args = iter_args(subject)
                if bound_method:
                    next(args)

                for name, argtype in zip(args, func.argtypes):
                    type_hints[name.arg] = getvalue(argtype)

            return type_hints
    except (OSError, TypeError):  # failed to load source code
        return {}
    except SyntaxError:  # failed to parse type_comments
        return {}


def update_annotations_using_type_comments(app: Sphinx, obj: Any, bound_method: bool) -> None:
    """Update annotations info of *obj* using type_comments."""
    if callable(obj) and hasattr(obj, '__annotations__'):
        type_hints = get_type_hints_from_type_comment(obj, bound_method)
        for key, typ in type_hints.items():
            obj.__annotations__[key] = typ


def setup(app: Sphinx) -> Dict[str, Any]:
    app.connect('autodoc-before-format-args', update_annotations_using_type_comments)

    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}
