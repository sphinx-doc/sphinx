"""
    sphinx.util.inspect
    ~~~~~~~~~~~~~~~~~~~

    Helpers for inspecting Python modules.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import builtins
import contextlib
import enum
import inspect
import re
import sys
import types
import typing
import warnings
from functools import partial, partialmethod
from inspect import (  # NOQA
    Parameter, isclass, ismethod, ismethoddescriptor, ismodule
)
from io import StringIO
from typing import Any, Callable, Dict, Mapping, List, Optional, Tuple
from typing import cast

from sphinx.deprecation import RemovedInSphinx40Warning, RemovedInSphinx50Warning
from sphinx.pycode.ast import ast  # for py35-37
from sphinx.pycode.ast import unparse as ast_unparse
from sphinx.util import logging
from sphinx.util.typing import ForwardRef
from sphinx.util.typing import stringify as stringify_annotation

if sys.version_info > (3, 7):
    from types import (
        ClassMethodDescriptorType,
        MethodDescriptorType,
        WrapperDescriptorType
    )
else:
    ClassMethodDescriptorType = type(object.__init__)
    MethodDescriptorType = type(str.join)
    WrapperDescriptorType = type(dict.__dict__['fromkeys'])

logger = logging.getLogger(__name__)

memory_address_re = re.compile(r' at 0x[0-9a-f]{8,16}(?=>)', re.IGNORECASE)


# Copied from the definition of inspect.getfullargspec from Python master,
# and modified to remove the use of special flags that break decorated
# callables and bound methods in the name of backwards compatibility. Used
# under the terms of PSF license v2, which requires the above statement
# and the following:
#
#   Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
#   2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017 Python Software
#   Foundation; All Rights Reserved
def getargspec(func: Callable) -> Any:
    """Like inspect.getfullargspec but supports bound methods, and wrapped
    methods."""
    warnings.warn('sphinx.ext.inspect.getargspec() is deprecated',
                  RemovedInSphinx50Warning, stacklevel=2)
    # On 3.5+, signature(int) or similar raises ValueError. On 3.4, it
    # succeeds with a bogus signature. We want a TypeError uniformly, to
    # match historical behavior.
    if (isinstance(func, type) and
            is_builtin_class_method(func, "__new__") and
            is_builtin_class_method(func, "__init__")):
        raise TypeError(
            "can't compute signature for built-in type {}".format(func))

    sig = inspect.signature(func)

    args = []
    varargs = None
    varkw = None
    kwonlyargs = []
    defaults = ()
    annotations = {}
    defaults = ()
    kwdefaults = {}

    if sig.return_annotation is not sig.empty:
        annotations['return'] = sig.return_annotation

    for param in sig.parameters.values():
        kind = param.kind
        name = param.name

        if kind is Parameter.POSITIONAL_ONLY:
            args.append(name)
        elif kind is Parameter.POSITIONAL_OR_KEYWORD:
            args.append(name)
            if param.default is not param.empty:
                defaults += (param.default,)  # type: ignore
        elif kind is Parameter.VAR_POSITIONAL:
            varargs = name
        elif kind is Parameter.KEYWORD_ONLY:
            kwonlyargs.append(name)
            if param.default is not param.empty:
                kwdefaults[name] = param.default
        elif kind is Parameter.VAR_KEYWORD:
            varkw = name

        if param.annotation is not param.empty:
            annotations[name] = param.annotation

    if not kwdefaults:
        # compatibility with 'func.__kwdefaults__'
        kwdefaults = None

    if not defaults:
        # compatibility with 'func.__defaults__'
        defaults = None

    return inspect.FullArgSpec(args, varargs, varkw, defaults,
                               kwonlyargs, kwdefaults, annotations)


def unwrap(obj: Any) -> Any:
    """Get an original object from wrapped object (wrapped functions)."""
    try:
        if hasattr(obj, '__sphinx_mock__'):
            # Skip unwrapping mock object to avoid RecursionError
            return obj
        else:
            return inspect.unwrap(obj)
    except ValueError:
        # might be a mock object
        return obj


def unwrap_all(obj: Any, *, stop: Callable = None) -> Any:
    """
    Get an original object from wrapped object (unwrapping partials, wrapped
    functions, and other decorators).
    """
    while True:
        if stop and stop(obj):
            return obj
        elif ispartial(obj):
            obj = obj.func
        elif inspect.isroutine(obj) and hasattr(obj, '__wrapped__'):
            obj = obj.__wrapped__
        elif isclassmethod(obj):
            obj = obj.__func__
        elif isstaticmethod(obj):
            obj = obj.__func__
        else:
            return obj


def isenumclass(x: Any) -> bool:
    """Check if the object is subclass of enum."""
    return inspect.isclass(x) and issubclass(x, enum.Enum)


def isenumattribute(x: Any) -> bool:
    """Check if the object is attribute of enum."""
    return isinstance(x, enum.Enum)


def unpartial(obj: Any) -> Any:
    """Get an original object from partial object.

    This returns given object itself if not partial.
    """
    while ispartial(obj):
        obj = obj.func

    return obj


def ispartial(obj: Any) -> bool:
    """Check if the object is partial."""
    return isinstance(obj, (partial, partialmethod))


def isclassmethod(obj: Any) -> bool:
    """Check if the object is classmethod."""
    if isinstance(obj, classmethod):
        return True
    elif inspect.ismethod(obj) and obj.__self__ is not None and isclass(obj.__self__):
        return True

    return False


def isstaticmethod(obj: Any, cls: Any = None, name: str = None) -> bool:
    """Check if the object is staticmethod."""
    if isinstance(obj, staticmethod):
        return True
    elif cls and name:
        # trace __mro__ if the method is defined in parent class
        #
        # .. note:: This only works well with new style classes.
        for basecls in getattr(cls, '__mro__', [cls]):
            meth = basecls.__dict__.get(name)
            if meth:
                if isinstance(meth, staticmethod):
                    return True
                else:
                    return False

    return False


def isdescriptor(x: Any) -> bool:
    """Check if the object is some kind of descriptor."""
    for item in '__get__', '__set__', '__delete__':
        if hasattr(safe_getattr(x, item, None), '__call__'):
            return True
    return False


def isabstractmethod(obj: Any) -> bool:
    """Check if the object is an abstractmethod."""
    return safe_getattr(obj, '__isabstractmethod__', False) is True


def is_cython_function_or_method(obj: Any) -> bool:
    """Check if the object is a function or method in cython."""
    try:
        return obj.__class__.__name__ == 'cython_function_or_method'
    except AttributeError:
        return False


def isattributedescriptor(obj: Any) -> bool:
    """Check if the object is an attribute like descriptor."""
    if inspect.isdatadescriptor(obj):
        # data descriptor is kind of attribute
        return True
    elif isdescriptor(obj):
        # non data descriptor
        unwrapped = unwrap(obj)
        if isfunction(unwrapped) or isbuiltin(unwrapped) or inspect.ismethod(unwrapped):
            # attribute must not be either function, builtin and method
            return False
        elif is_cython_function_or_method(unwrapped):
            # attribute must not be either function and method (for cython)
            return False
        elif inspect.isclass(unwrapped):
            # attribute must not be a class
            return False
        elif isinstance(unwrapped, (ClassMethodDescriptorType,
                                    MethodDescriptorType,
                                    WrapperDescriptorType)):
            # attribute must not be a method descriptor
            return False
        elif type(unwrapped).__name__ == "instancemethod":
            # attribute must not be an instancemethod (C-API)
            return False
        else:
            return True
    else:
        return False


def is_singledispatch_function(obj: Any) -> bool:
    """Check if the object is singledispatch function."""
    if (inspect.isfunction(obj) and
            hasattr(obj, 'dispatch') and
            hasattr(obj, 'register') and
            obj.dispatch.__module__ == 'functools'):
        return True
    else:
        return False


def is_singledispatch_method(obj: Any) -> bool:
    """Check if the object is singledispatch method."""
    try:
        from functools import singledispatchmethod  # type: ignore
        return isinstance(obj, singledispatchmethod)
    except ImportError:  # py35-37
        return False


def isfunction(obj: Any) -> bool:
    """Check if the object is function."""
    return inspect.isfunction(unwrap_all(obj))


def isbuiltin(obj: Any) -> bool:
    """Check if the object is builtin."""
    return inspect.isbuiltin(unwrap_all(obj))


def isroutine(obj: Any) -> bool:
    """Check is any kind of function or method."""
    return inspect.isroutine(unwrap_all(obj))


def iscoroutinefunction(obj: Any) -> bool:
    """Check if the object is coroutine-function."""
    # unwrap staticmethod, classmethod and partial (except wrappers)
    obj = unwrap_all(obj, stop=lambda o: hasattr(o, '__wrapped__'))
    if hasattr(obj, '__code__') and inspect.iscoroutinefunction(obj):
        # check obj.__code__ because iscoroutinefunction() crashes for custom method-like
        # objects (see https://github.com/sphinx-doc/sphinx/issues/6605)
        return True
    else:
        return False


def isproperty(obj: Any) -> bool:
    """Check if the object is property."""
    if sys.version_info > (3, 8):
        from functools import cached_property  # cached_property is available since py3.8
        if isinstance(obj, cached_property):
            return True

    return isinstance(obj, property)


def isgenericalias(obj: Any) -> bool:
    """Check if the object is GenericAlias."""
    if (hasattr(typing, '_GenericAlias') and  # only for py37+
            isinstance(obj, typing._GenericAlias)):  # type: ignore
        return True
    elif (hasattr(types, 'GenericAlias') and  # only for py39+
          isinstance(obj, types.GenericAlias)):  # type: ignore
        return True
    else:
        return False


def safe_getattr(obj: Any, name: str, *defargs: Any) -> Any:
    """A getattr() that turns all exceptions into AttributeErrors."""
    try:
        return getattr(obj, name, *defargs)
    except Exception as exc:
        # sometimes accessing a property raises an exception (e.g.
        # NotImplementedError), so let's try to read the attribute directly
        try:
            # In case the object does weird things with attribute access
            # such that accessing `obj.__dict__` may raise an exception
            return obj.__dict__[name]
        except Exception:
            pass

        # this is a catch-all for all the weird things that some modules do
        # with attribute access
        if defargs:
            return defargs[0]

        raise AttributeError(name) from exc


def safe_getmembers(object: Any, predicate: Callable[[str], bool] = None,
                    attr_getter: Callable = safe_getattr) -> List[Tuple[str, Any]]:
    """A version of inspect.getmembers() that uses safe_getattr()."""
    warnings.warn('safe_getmembers() is deprecated', RemovedInSphinx40Warning, stacklevel=2)

    results = []  # type: List[Tuple[str, Any]]
    for key in dir(object):
        try:
            value = attr_getter(object, key, None)
        except AttributeError:
            continue
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results


def object_description(object: Any) -> str:
    """A repr() implementation that returns text safe to use in reST context."""
    if isinstance(object, dict):
        try:
            sorted_keys = sorted(object)
        except Exception:
            pass  # Cannot sort dict keys, fall back to generic repr
        else:
            items = ("%s: %s" %
                     (object_description(key), object_description(object[key]))
                     for key in sorted_keys)
            return "{%s}" % ", ".join(items)
    if isinstance(object, set):
        try:
            sorted_values = sorted(object)
        except TypeError:
            pass  # Cannot sort set values, fall back to generic repr
        else:
            return "{%s}" % ", ".join(object_description(x) for x in sorted_values)
    if isinstance(object, frozenset):
        try:
            sorted_values = sorted(object)
        except TypeError:
            pass  # Cannot sort frozenset values, fall back to generic repr
        else:
            return "frozenset({%s})" % ", ".join(object_description(x)
                                                 for x in sorted_values)
    try:
        s = repr(object)
    except Exception as exc:
        raise ValueError from exc
    # Strip non-deterministic memory addresses such as
    # ``<__main__.A at 0x7f68cb685710>``
    s = memory_address_re.sub('', s)
    return s.replace('\n', ' ')


def is_builtin_class_method(obj: Any, attr_name: str) -> bool:
    """If attr_name is implemented at builtin class, return True.

        >>> is_builtin_class_method(int, '__init__')
        True

    Why this function needed? CPython implements int.__init__ by Descriptor
    but PyPy implements it by pure Python code.
    """
    try:
        mro = inspect.getmro(obj)
    except AttributeError:
        # no __mro__, assume the object has no methods as we know them
        return False

    try:
        cls = next(c for c in mro if attr_name in safe_getattr(c, '__dict__', {}))
    except StopIteration:
        return False

    try:
        name = safe_getattr(cls, '__name__')
    except AttributeError:
        return False

    return getattr(builtins, name, None) is cls


def _should_unwrap(subject: Callable) -> bool:
    """Check the function should be unwrapped on getting signature."""
    if (safe_getattr(subject, '__globals__', None) and
            subject.__globals__.get('__name__') == 'contextlib' and  # type: ignore
            subject.__globals__.get('__file__') == contextlib.__file__):  # type: ignore
        # contextmanger should be unwrapped
        return True

    return False


def signature(subject: Callable, bound_method: bool = False, follow_wrapped: bool = False,
              type_aliases: Dict = {}) -> inspect.Signature:
    """Return a Signature object for the given *subject*.

    :param bound_method: Specify *subject* is a bound method or not
    :param follow_wrapped: Same as ``inspect.signature()``.
                           Defaults to ``False`` (get a signature of *subject*).
    """
    try:
        try:
            if _should_unwrap(subject):
                signature = inspect.signature(subject)
            else:
                signature = inspect.signature(subject, follow_wrapped=follow_wrapped)
        except ValueError:
            # follow built-in wrappers up (ex. functools.lru_cache)
            signature = inspect.signature(subject)
        parameters = list(signature.parameters.values())
        return_annotation = signature.return_annotation
    except IndexError:
        # Until python 3.6.4, cpython has been crashed on inspection for
        # partialmethods not having any arguments.
        # https://bugs.python.org/issue33009
        if hasattr(subject, '_partialmethod'):
            parameters = []
            return_annotation = Parameter.empty
        else:
            raise

    try:
        # Update unresolved annotations using ``get_type_hints()``.
        annotations = typing.get_type_hints(subject, None, type_aliases)
        for i, param in enumerate(parameters):
            if isinstance(param.annotation, str) and param.name in annotations:
                parameters[i] = param.replace(annotation=annotations[param.name])
        if 'return' in annotations:
            return_annotation = annotations['return']
    except Exception:
        # ``get_type_hints()`` does not support some kind of objects like partial,
        # ForwardRef and so on.
        pass

    if bound_method:
        if inspect.ismethod(subject):
            # ``inspect.signature()`` considers the subject is a bound method and removes
            # first argument from signature.  Therefore no skips are needed here.
            pass
        else:
            if len(parameters) > 0:
                parameters.pop(0)

    # To allow to create signature object correctly for pure python functions,
    # pass an internal parameter __validate_parameters__=False to Signature
    #
    # For example, this helps a function having a default value `inspect._empty`.
    # refs: https://github.com/sphinx-doc/sphinx/issues/7935
    return inspect.Signature(parameters, return_annotation=return_annotation,  # type: ignore
                             __validate_parameters__=False)


def evaluate_signature(sig: inspect.Signature, globalns: Dict = None, localns: Dict = None
                       ) -> inspect.Signature:
    """Evaluate unresolved type annotations in a signature object."""
    def evaluate_forwardref(ref: ForwardRef, globalns: Dict, localns: Dict) -> Any:
        """Evaluate a forward reference."""
        if sys.version_info > (3, 9):
            return ref._evaluate(globalns, localns, frozenset())
        else:
            return ref._evaluate(globalns, localns)

    def evaluate(annotation: Any, globalns: Dict, localns: Dict) -> Any:
        """Evaluate unresolved type annotation."""
        try:
            if isinstance(annotation, str):
                ref = ForwardRef(annotation, True)
                annotation = evaluate_forwardref(ref, globalns, localns)

                if isinstance(annotation, ForwardRef):
                    annotation = evaluate_forwardref(ref, globalns, localns)
                elif isinstance(annotation, str):
                    # might be a ForwardRef'ed annotation in overloaded functions
                    ref = ForwardRef(annotation, True)
                    annotation = evaluate_forwardref(ref, globalns, localns)
        except (NameError, TypeError):
            # failed to evaluate type. skipped.
            pass

        return annotation

    if globalns is None:
        globalns = {}
    if localns is None:
        localns = globalns

    parameters = list(sig.parameters.values())
    for i, param in enumerate(parameters):
        if param.annotation:
            annotation = evaluate(param.annotation, globalns, localns)
            parameters[i] = param.replace(annotation=annotation)

    return_annotation = sig.return_annotation
    if return_annotation:
        return_annotation = evaluate(return_annotation, globalns, localns)

    return sig.replace(parameters=parameters, return_annotation=return_annotation)


def stringify_signature(sig: inspect.Signature, show_annotation: bool = True,
                        show_return_annotation: bool = True) -> str:
    """Stringify a Signature object.

    :param show_annotation: Show annotation in result
    """
    args = []
    last_kind = None
    for param in sig.parameters.values():
        if param.kind != param.POSITIONAL_ONLY and last_kind == param.POSITIONAL_ONLY:
            # PEP-570: Separator for Positional Only Parameter: /
            args.append('/')
        if param.kind == param.KEYWORD_ONLY and last_kind in (param.POSITIONAL_OR_KEYWORD,
                                                              param.POSITIONAL_ONLY,
                                                              None):
            # PEP-3102: Separator for Keyword Only Parameter: *
            args.append('*')

        arg = StringIO()
        if param.kind == param.VAR_POSITIONAL:
            arg.write('*' + param.name)
        elif param.kind == param.VAR_KEYWORD:
            arg.write('**' + param.name)
        else:
            arg.write(param.name)

        if show_annotation and param.annotation is not param.empty:
            arg.write(': ')
            arg.write(stringify_annotation(param.annotation))
        if param.default is not param.empty:
            if show_annotation and param.annotation is not param.empty:
                arg.write(' = ')
            else:
                arg.write('=')
            arg.write(object_description(param.default))

        args.append(arg.getvalue())
        last_kind = param.kind

    if last_kind == Parameter.POSITIONAL_ONLY:
        # PEP-570: Separator for Positional Only Parameter: /
        args.append('/')

    if (sig.return_annotation is Parameter.empty or
            show_annotation is False or
            show_return_annotation is False):
        return '(%s)' % ', '.join(args)
    else:
        annotation = stringify_annotation(sig.return_annotation)
        return '(%s) -> %s' % (', '.join(args), annotation)


def signature_from_str(signature: str) -> inspect.Signature:
    """Create a Signature object from string."""
    code = 'def func' + signature + ': pass'
    module = ast.parse(code)
    function = cast(ast.FunctionDef, module.body[0])  # type: ignore

    return signature_from_ast(function, code)


def signature_from_ast(node: ast.FunctionDef, code: str = '') -> inspect.Signature:
    """Create a Signature object from AST *node*."""
    args = node.args
    defaults = list(args.defaults)
    params = []
    if hasattr(args, "posonlyargs"):
        posonlyargs = len(args.posonlyargs)  # type: ignore
        positionals = posonlyargs + len(args.args)
    else:
        posonlyargs = 0
        positionals = len(args.args)

    for _ in range(len(defaults), positionals):
        defaults.insert(0, Parameter.empty)

    if hasattr(args, "posonlyargs"):
        for i, arg in enumerate(args.posonlyargs):  # type: ignore
            if defaults[i] is Parameter.empty:
                default = Parameter.empty
            else:
                default = ast_unparse(defaults[i], code)

            annotation = ast_unparse(arg.annotation, code) or Parameter.empty
            params.append(Parameter(arg.arg, Parameter.POSITIONAL_ONLY,
                                    default=default, annotation=annotation))

    for i, arg in enumerate(args.args):
        if defaults[i + posonlyargs] is Parameter.empty:
            default = Parameter.empty
        else:
            default = ast_unparse(defaults[i + posonlyargs], code)

        annotation = ast_unparse(arg.annotation, code) or Parameter.empty
        params.append(Parameter(arg.arg, Parameter.POSITIONAL_OR_KEYWORD,
                                default=default, annotation=annotation))

    if args.vararg:
        annotation = ast_unparse(args.vararg.annotation, code) or Parameter.empty
        params.append(Parameter(args.vararg.arg, Parameter.VAR_POSITIONAL,
                                annotation=annotation))

    for i, arg in enumerate(args.kwonlyargs):
        default = ast_unparse(args.kw_defaults[i], code) or Parameter.empty
        annotation = ast_unparse(arg.annotation, code) or Parameter.empty
        params.append(Parameter(arg.arg, Parameter.KEYWORD_ONLY, default=default,
                                annotation=annotation))

    if args.kwarg:
        annotation = ast_unparse(args.kwarg.annotation, code) or Parameter.empty
        params.append(Parameter(args.kwarg.arg, Parameter.VAR_KEYWORD,
                                annotation=annotation))

    return_annotation = ast_unparse(node.returns, code) or Parameter.empty

    return inspect.Signature(params, return_annotation=return_annotation)


class Signature:
    """The Signature object represents the call signature of a callable object and
    its return annotation.
    """

    empty = inspect.Signature.empty

    def __init__(self, subject: Callable, bound_method: bool = False,
                 has_retval: bool = True) -> None:
        warnings.warn('sphinx.util.inspect.Signature() is deprecated',
                      RemovedInSphinx40Warning, stacklevel=2)

        # check subject is not a built-in class (ex. int, str)
        if (isinstance(subject, type) and
                is_builtin_class_method(subject, "__new__") and
                is_builtin_class_method(subject, "__init__")):
            raise TypeError("can't compute signature for built-in type {}".format(subject))

        self.subject = subject
        self.has_retval = has_retval
        self.partialmethod_with_noargs = False

        try:
            self.signature = inspect.signature(subject)  # type: Optional[inspect.Signature]
        except IndexError:
            # Until python 3.6.4, cpython has been crashed on inspection for
            # partialmethods not having any arguments.
            # https://bugs.python.org/issue33009
            if hasattr(subject, '_partialmethod'):
                self.signature = None
                self.partialmethod_with_noargs = True
            else:
                raise

        try:
            self.annotations = typing.get_type_hints(subject)
        except Exception:
            # get_type_hints() does not support some kind of objects like partial,
            # ForwardRef and so on.  For them, it raises an exception. In that case,
            # we try to build annotations from argspec.
            self.annotations = {}

        if bound_method:
            # client gives a hint that the subject is a bound method

            if inspect.ismethod(subject):
                # inspect.signature already considers the subject is bound method.
                # So it is not need to skip first argument.
                self.skip_first_argument = False
            else:
                self.skip_first_argument = True
        else:
            # inspect.signature recognizes type of method properly without any hints
            self.skip_first_argument = False

    @property
    def parameters(self) -> Mapping:
        if self.partialmethod_with_noargs:
            return {}
        else:
            return self.signature.parameters

    @property
    def return_annotation(self) -> Any:
        if self.signature:
            if self.has_retval:
                return self.signature.return_annotation
            else:
                return Parameter.empty
        else:
            return None

    def format_args(self, show_annotation: bool = True) -> str:
        def get_annotation(param: Parameter) -> Any:
            if isinstance(param.annotation, str) and param.name in self.annotations:
                return self.annotations[param.name]
            else:
                return param.annotation

        args = []
        last_kind = None
        for i, param in enumerate(self.parameters.values()):
            # skip first argument if subject is bound method
            if self.skip_first_argument and i == 0:
                continue

            arg = StringIO()

            # insert '*' between POSITIONAL args and KEYWORD_ONLY args::
            #     func(a, b, *, c, d):
            if param.kind == param.KEYWORD_ONLY and last_kind in (param.POSITIONAL_OR_KEYWORD,
                                                                  param.POSITIONAL_ONLY,
                                                                  None):
                args.append('*')

            if param.kind in (param.POSITIONAL_ONLY,
                              param.POSITIONAL_OR_KEYWORD,
                              param.KEYWORD_ONLY):
                arg.write(param.name)
                if show_annotation and param.annotation is not param.empty:
                    arg.write(': ')
                    arg.write(stringify_annotation(get_annotation(param)))
                if param.default is not param.empty:
                    if param.annotation is param.empty or show_annotation is False:
                        arg.write('=')
                        arg.write(object_description(param.default))
                    else:
                        arg.write(' = ')
                        arg.write(object_description(param.default))
            elif param.kind == param.VAR_POSITIONAL:
                arg.write('*')
                arg.write(param.name)
                if show_annotation and param.annotation is not param.empty:
                    arg.write(': ')
                    arg.write(stringify_annotation(get_annotation(param)))
            elif param.kind == param.VAR_KEYWORD:
                arg.write('**')
                arg.write(param.name)
                if show_annotation and param.annotation is not param.empty:
                    arg.write(': ')
                    arg.write(stringify_annotation(get_annotation(param)))

            args.append(arg.getvalue())
            last_kind = param.kind

        if self.return_annotation is Parameter.empty or show_annotation is False:
            return '(%s)' % ', '.join(args)
        else:
            if 'return' in self.annotations:
                annotation = stringify_annotation(self.annotations['return'])
            else:
                annotation = stringify_annotation(self.return_annotation)

            return '(%s) -> %s' % (', '.join(args), annotation)

    def format_annotation(self, annotation: Any) -> str:
        """Return formatted representation of a type annotation."""
        return stringify_annotation(annotation)

    def format_annotation_new(self, annotation: Any) -> str:
        """format_annotation() for py37+"""
        return stringify_annotation(annotation)

    def format_annotation_old(self, annotation: Any) -> str:
        """format_annotation() for py36 or below"""
        return stringify_annotation(annotation)


def getdoc(obj: Any, attrgetter: Callable = safe_getattr,
           allow_inherited: bool = False, cls: Any = None, name: str = None) -> str:
    """Get the docstring for the object.

    This tries to obtain the docstring for some kind of objects additionally:

    * partial functions
    * inherited docstring
    * inherited decorated methods
    """
    doc = attrgetter(obj, '__doc__', None)
    if ispartial(obj) and doc == obj.__class__.__doc__:
        return getdoc(obj.func)
    elif doc is None and allow_inherited:
        doc = inspect.getdoc(obj)

        if doc is None and cls:
            # inspect.getdoc() does not support some kind of inherited and decorated methods.
            # This tries to obtain the docstring from super classes.
            for basecls in getattr(cls, '__mro__', []):
                meth = safe_getattr(basecls, name, None)
                if meth is not None:
                    doc = inspect.getdoc(meth)
                    if doc:
                        break

    return doc
