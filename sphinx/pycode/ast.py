"""
    sphinx.pycode.ast
    ~~~~~~~~~~~~~~~~~

    Helpers for AST (Abstract Syntax Tree).

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

if sys.version_info > (3, 8):
    import ast
else:
    try:
        # use typed_ast module if installed
        from typed_ast import ast3 as ast
    except ImportError:
        import ast  # type: ignore


def parse(code: str, mode: str = 'exec') -> "ast.AST":
    """Parse the *code* using built-in ast or typed_ast.

    This enables "type_comments" feature if possible.
    """
    try:
        # type_comments parameter is available on py38+
        return ast.parse(code, mode=mode, type_comments=True)  # type: ignore
    except TypeError:
        # fallback to ast module.
        # typed_ast is used to parse type_comments if installed.
        return ast.parse(code, mode=mode)


def unparse(node: ast.AST) -> str:
    """Unparse an AST to string."""
    if node is None:
        return None
    elif isinstance(node, str):
        return node
    elif isinstance(node, ast.Attribute):
        return "%s.%s" % (unparse(node.value), node.attr)
    elif isinstance(node, ast.Bytes):
        return repr(node.s)
    elif isinstance(node, ast.Call):
        args = ([unparse(e) for e in node.args] +
                ["%s=%s" % (k.arg, unparse(k.value)) for k in node.keywords])
        return "%s(%s)" % (unparse(node.func), ", ".join(args))
    elif isinstance(node, ast.Dict):
        keys = (unparse(k) for k in node.keys)
        values = (unparse(v) for v in node.values)
        items = (k + ": " + v for k, v in zip(keys, values))
        return "{" + ", ".join(items) + "}"
    elif isinstance(node, ast.Ellipsis):
        return "..."
    elif isinstance(node, ast.Index):
        return unparse(node.value)
    elif isinstance(node, ast.Lambda):
        return "<function <lambda>>"  # TODO
    elif isinstance(node, ast.List):
        return "[" + ", ".join(unparse(e) for e in node.elts) + "]"
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.NameConstant):
        return repr(node.value)
    elif isinstance(node, ast.Num):
        return repr(node.n)
    elif isinstance(node, ast.Set):
        return "{" + ", ".join(unparse(e) for e in node.elts) + "}"
    elif isinstance(node, ast.Str):
        return repr(node.s)
    elif isinstance(node, ast.Subscript):
        return "%s[%s]" % (unparse(node.value), unparse(node.slice))
    elif isinstance(node, ast.Tuple):
        return ", ".join(unparse(e) for e in node.elts)
    elif sys.version_info > (3, 6) and isinstance(node, ast.Constant):
        # this branch should be placed at last
        return repr(node.value)
    else:
        raise NotImplementedError('Unable to parse %s object' % type(node).__name__)
