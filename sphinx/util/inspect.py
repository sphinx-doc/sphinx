"""Helpers for inspecting Python modules."""

from __future__ import annotations

import ast
import builtins
import contextlib
import enum
import inspect
import re
import sys
import types
import typing
from collections.abc import Mapping
from functools import cached_property, partial, partialmethod, singledispatchmethod
from importlib import import_module
from inspect import Parameter, isclass
from io import StringIO
from types import ClassMethodDescriptorType, MethodDescriptorType, WrapperDescriptorType
from typing import TYPE_CHECKING, Any

from sphinx.pycode.ast import unparse as ast_unparse
from sphinx.util import logging
from sphinx.util.typing import ForwardRef, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from types import MethodType, ModuleType

logger = logging.getLogger(__name__)

memory_address_re = re.compile(r' at 0x[0-9a-f]{8,16}(?=>)', re.IGNORECASE)

# re-export
isasyncgenfunction = inspect.isasyncgenfunction
ismethod = inspect.ismethod
ismethoddescriptor = inspect.ismethoddescriptor
isclass = inspect.isclass  # NoQA: F811
ismodule = inspect.ismodule


def unwrap(obj: Any) -> Any:
    """Get an original object from wrapped object (wrapped functions)."""
    if hasattr(obj, '__sphinx_mock__'):
        # Skip unwrapping mock object to avoid RecursionError
        return obj

    try:
        return inspect.unwrap(obj)
    except ValueError:
        # might be a mock object
        return obj


def unwrap_all(obj: Any, *, stop: Callable[[Any], bool] | None = None) -> Any:
    """
    Get an original object from wrapped object (unwrapping partials, wrapped
    functions, and other decorators).
    """
    while True:
        if stop and stop(obj):
            return obj

        if ispartial(obj):
            obj = obj.func
        elif inspect.isroutine(obj) and hasattr(obj, '__wrapped__'):
            obj = obj.__wrapped__
        elif isclassmethod(obj) or isstaticmethod(obj):
            obj = obj.__func__
        else:
            return obj


def getall(obj: Any) -> Sequence[str] | None:
    """Get __all__ attribute of the module as dict.

    Return None if given *obj* does not have __all__.
    Raises ValueError if given *obj* have invalid __all__.
    """
    __all__ = safe_getattr(obj, '__all__', None)
    if __all__ is None:
        return None
    if isinstance(__all__, (list, tuple)) and all(isinstance(e, str) for e in __all__):
        return __all__
    raise ValueError(__all__)


def getannotations(obj: Any) -> Mapping[str, Any]:
    """Get __annotations__ from given *obj* safely."""
    if sys.version_info >= (3, 10, 0) or not isinstance(obj, type):
        __annotations__ = safe_getattr(obj, '__annotations__', None)
    else:
        # Workaround for bugfix not available until python 3.10 as recommended by docs
        # https://docs.python.org/3.10/howto/annotations.html#accessing-the-annotations-dict-of-an-object-in-python-3-9-and-older
        __dict__ = safe_getattr(obj, '__dict__', {})
        __annotations__ = __dict__.get('__annotations__', None)
    if isinstance(__annotations__, Mapping):
        return __annotations__
    return {}


def getglobals(obj: Any) -> Mapping[str, Any]:
    """Get __globals__ from given *obj* safely."""
    __globals__ = safe_getattr(obj, '__globals__', None)
    if isinstance(__globals__, Mapping):
        return __globals__
    return {}


def getmro(obj: Any) -> tuple[type, ...]:
    """Get __mro__ from given *obj* safely."""
    __mro__ = safe_getattr(obj, '__mro__', None)
    if isinstance(__mro__, tuple):
        return __mro__
    return ()


def getorigbases(obj: Any) -> tuple[Any, ...] | None:
    """Get __orig_bases__ from *obj* safely."""
    if not inspect.isclass(obj):
        return None

    # Get __orig_bases__ from obj.__dict__ to avoid accessing the parent's __orig_bases__.
    # refs: https://github.com/sphinx-doc/sphinx/issues/9607
    __dict__ = safe_getattr(obj, '__dict__', {})
    __orig_bases__ = __dict__.get('__orig_bases__')
    if isinstance(__orig_bases__, tuple) and len(__orig_bases__) > 0:
        return __orig_bases__
    return None


def getslots(obj: Any) -> dict[str, Any] | None:
    """Get __slots__ attribute of the class as dict.

    Return None if gienv *obj* does not have __slots__.
    Raises TypeError if given *obj* is not a class.
    Raises ValueError if given *obj* have invalid __slots__.
    """
    if not inspect.isclass(obj):
        raise TypeError

    __slots__ = safe_getattr(obj, '__slots__', None)
    if __slots__ is None:
        return None
    elif isinstance(__slots__, dict):
        return __slots__
    elif isinstance(__slots__, str):
        return {__slots__: None}
    elif isinstance(__slots__, (list, tuple)):
        return dict.fromkeys(__slots__)
    else:
        raise ValueError


def isNewType(obj: Any) -> bool:
    """Check the if object is a kind of NewType."""
    if sys.version_info[:2] >= (3, 10):
        return isinstance(obj, typing.NewType)
    __module__ = safe_getattr(obj, '__module__', None)
    __qualname__ = safe_getattr(obj, '__qualname__', None)
    return __module__ == 'typing' and __qualname__ == 'NewType.<locals>.new_type'


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


def isclassmethod(obj: Any, cls: Any = None, name: str | None = None) -> bool:
    """Check if the object is classmethod."""
    if isinstance(obj, classmethod):
        return True
    if inspect.ismethod(obj) and obj.__self__ is not None and isclass(obj.__self__):
        return True
    if cls and name:
        # trace __mro__ if the method is defined in parent class
        sentinel = object()
        for basecls in getmro(cls):
            meth = basecls.__dict__.get(name, sentinel)
            if meth is not sentinel:
                return isclassmethod(meth)
    return False


def isstaticmethod(obj: Any, cls: Any = None, name: str | None = None) -> bool:
    """Check if the object is staticmethod."""
    if isinstance(obj, staticmethod):
        return True
    if cls and name:
        # trace __mro__ if the method is defined in parent class
        sentinel = object()
        for basecls in getattr(cls, '__mro__', [cls]):
            meth = basecls.__dict__.get(name, sentinel)
            if meth is not sentinel:
                return isinstance(meth, staticmethod)
    return False


def isdescriptor(x: Any) -> bool:
    """Check if the object is some kind of descriptor."""
    return any(
        callable(safe_getattr(x, item, None)) for item in ('__get__', '__set__', '__delete__')
    )


def isabstractmethod(obj: Any) -> bool:
    """Check if the object is an abstractmethod."""
    return safe_getattr(obj, '__isabstractmethod__', False) is True


def isboundmethod(method: MethodType) -> bool:
    """Check if the method is a bound method."""
    return safe_getattr(method, '__self__', None) is not None


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
    if isdescriptor(obj):
        # non data descriptor
        unwrapped = unwrap(obj)
        if isfunction(unwrapped) or isbuiltin(unwrapped) or inspect.ismethod(unwrapped):
            # attribute must not be either function, builtin and method
            return False
        if is_cython_function_or_method(unwrapped):
            # attribute must not be either function and method (for cython)
            return False
        if inspect.isclass(unwrapped):
            # attribute must not be a class
            return False
        if isinstance(
            unwrapped, (ClassMethodDescriptorType, MethodDescriptorType, WrapperDescriptorType)
        ):
            # attribute must not be a method descriptor
            return False
        # attribute must not be an instancemethod (C-API)
        return type(unwrapped).__name__ != 'instancemethod'
    return False


def is_singledispatch_function(obj: Any) -> bool:
    """Check if the object is singledispatch function."""
    return (
        inspect.isfunction(obj)
        and hasattr(obj, 'dispatch')
        and hasattr(obj, 'register')
        and obj.dispatch.__module__ == 'functools'
    )


def is_singledispatch_method(obj: Any) -> bool:
    """Check if the object is singledispatch method."""
    return isinstance(obj, singledispatchmethod)


def isfunction(obj: Any) -> bool:
    """Check if the object is function."""
    return inspect.isfunction(unpartial(obj))


def isbuiltin(obj: Any) -> bool:
    """Check if the object is function."""
    return inspect.isbuiltin(unpartial(obj))


def isroutine(obj: Any) -> bool:
    """Check is any kind of function or method."""
    return inspect.isroutine(unpartial(obj))


def iscoroutinefunction(obj: Any) -> bool:
    """Check if the object is coroutine-function."""

    def iswrappedcoroutine(obj: Any) -> bool:
        """Check if the object is wrapped coroutine-function."""
        if isstaticmethod(obj) or isclassmethod(obj) or ispartial(obj):
            # staticmethod, classmethod and partial method are not a wrapped coroutine-function
            # Note: Since 3.10, staticmethod and classmethod becomes a kind of wrappers
            return False
        return hasattr(obj, '__wrapped__')

    obj = unwrap_all(obj, stop=iswrappedcoroutine)
    return inspect.iscoroutinefunction(obj)


def isproperty(obj: Any) -> bool:
    """Check if the object is property."""
    return isinstance(obj, (property, cached_property))


def isgenericalias(obj: Any) -> bool:
    """Check if the object is GenericAlias."""
    return isinstance(obj, (types.GenericAlias, typing._BaseGenericAlias))  # type: ignore[attr-defined]


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


def object_description(obj: Any, *, _seen: frozenset[int] = frozenset()) -> str:
    """A repr() implementation that returns text safe to use in reST context.

    Maintains a set of 'seen' object IDs to detect and avoid infinite recursion.
    """
    seen = _seen
    if isinstance(obj, dict):
        if id(obj) in seen:
            return 'dict(...)'
        seen |= {id(obj)}
        try:
            sorted_keys = sorted(obj)
        except TypeError:
            # Cannot sort dict keys, fall back to using descriptions as a sort key
            sorted_keys = sorted(obj, key=lambda k: object_description(k, _seen=seen))

        items = (
            (object_description(key, _seen=seen), object_description(obj[key], _seen=seen))
            for key in sorted_keys
        )
        return '{%s}' % ', '.join(f'{key}: {value}' for (key, value) in items)
    elif isinstance(obj, set):
        if id(obj) in seen:
            return 'set(...)'
        seen |= {id(obj)}
        try:
            sorted_values = sorted(obj)
        except TypeError:
            # Cannot sort set values, fall back to using descriptions as a sort key
            sorted_values = sorted(obj, key=lambda x: object_description(x, _seen=seen))
        return '{%s}' % ', '.join(object_description(x, _seen=seen) for x in sorted_values)
    elif isinstance(obj, frozenset):
        if id(obj) in seen:
            return 'frozenset(...)'
        seen |= {id(obj)}
        try:
            sorted_values = sorted(obj)
        except TypeError:
            # Cannot sort frozenset values, fall back to using descriptions as a sort key
            sorted_values = sorted(obj, key=lambda x: object_description(x, _seen=seen))
        return 'frozenset({%s})' % ', '.join(
            object_description(x, _seen=seen) for x in sorted_values
        )
    elif isinstance(obj, enum.Enum):
        if obj.__repr__.__func__ is not enum.Enum.__repr__:  # type: ignore[attr-defined]
            return repr(obj)
        return f'{obj.__class__.__name__}.{obj.name}'
    elif isinstance(obj, tuple):
        if id(obj) in seen:
            return 'tuple(...)'
        seen |= frozenset([id(obj)])
        return '({}{})'.format(
            ', '.join(object_description(x, _seen=seen) for x in obj),
            ',' * (len(obj) == 1),
        )
    elif isinstance(obj, list):
        if id(obj) in seen:
            return 'list(...)'
        seen |= {id(obj)}
        return '[%s]' % ', '.join(object_description(x, _seen=seen) for x in obj)

    try:
        s = repr(obj)
    except Exception as exc:
        raise ValueError from exc
    # Strip non-deterministic memory addresses such as
    # ``<__main__.A at 0x7f68cb685710>``
    s = memory_address_re.sub('', s)
    return s.replace('\n', ' ')


def is_builtin_class_method(obj: Any, attr_name: str) -> bool:
    """attr_name is implemented at builtin class, return True.

        >>> is_builtin_class_method(int, '__init__')
        True

    Why this function needed? CPython implements int.__init__ by Descriptor
    but PyPy implements it by pure Python code.
    """
    mro = getmro(obj)

    try:
        cls = next(c for c in mro if attr_name in safe_getattr(c, '__dict__', {}))
    except StopIteration:
        return False

    try:
        name = safe_getattr(cls, '__name__')
    except AttributeError:
        return False

    return getattr(builtins, name, None) is cls


class DefaultValue:
    """A simple wrapper for default value of the parameters of overload functions."""

    def __init__(self, value: str) -> None:
        self.value = value

    def __eq__(self, other: object) -> bool:
        return self.value == other

    def __repr__(self) -> str:
        return self.value


class TypeAliasForwardRef:
    """Pseudo typing class for autodoc_type_aliases.

    This avoids the error on evaluating the type inside `get_type_hints()`.
    """

    def __init__(self, name: str) -> None:
        self.name = name

    def __call__(self) -> None:
        # Dummy method to imitate special typing classes
        pass

    def __eq__(self, other: Any) -> bool:
        return self.name == other

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return self.name


class TypeAliasModule:
    """Pseudo module class for autodoc_type_aliases."""

    def __init__(self, modname: str, mapping: dict[str, str]) -> None:
        self.__modname = modname
        self.__mapping = mapping

        self.__module: ModuleType | None = None

    def __getattr__(self, name: str) -> Any:
        fullname = '.'.join(filter(None, [self.__modname, name]))
        if fullname in self.__mapping:
            # exactly matched
            return TypeAliasForwardRef(self.__mapping[fullname])
        else:
            prefix = fullname + '.'
            nested = {k: v for k, v in self.__mapping.items() if k.startswith(prefix)}
            if nested:
                # sub modules or classes found
                return TypeAliasModule(fullname, nested)
            else:
                # no sub modules or classes found.
                try:
                    # return the real submodule if exists
                    return import_module(fullname)
                except ImportError:
                    # return the real class
                    if self.__module is None:
                        self.__module = import_module(self.__modname)

                    return getattr(self.__module, name)


class TypeAliasNamespace(dict[str, Any]):
    """Pseudo namespace class for autodoc_type_aliases.

    This enables to look up nested modules and classes like `mod1.mod2.Class`.
    """

    def __init__(self, mapping: Mapping[str, str]) -> None:
        super().__init__()
        self.__mapping = mapping

    def __getitem__(self, key: str) -> Any:
        if key in self.__mapping:
            # exactly matched
            return TypeAliasForwardRef(self.__mapping[key])
        else:
            prefix = key + '.'
            nested = {k: v for k, v in self.__mapping.items() if k.startswith(prefix)}
            if nested:
                # sub modules or classes found
                return TypeAliasModule(key, nested)
            else:
                raise KeyError


def _should_unwrap(subject: Callable) -> bool:
    """Check the function should be unwrapped on getting signature."""
    __globals__ = getglobals(subject)
    # contextmanger should be unwrapped
    return (
        __globals__.get('__name__') == 'contextlib'
        and __globals__.get('__file__') == contextlib.__file__
    )


def signature(
    subject: Callable,
    bound_method: bool = False,
    type_aliases: Mapping[str, str] | None = None,
) -> inspect.Signature:
    """Return a Signature object for the given *subject*.

    :param bound_method: Specify *subject* is a bound method or not
    """
    if type_aliases is None:
        type_aliases = {}

    try:
        if _should_unwrap(subject):
            signature = inspect.signature(subject)
        else:
            signature = inspect.signature(subject, follow_wrapped=True)
    except ValueError:
        # follow built-in wrappers up (ex. functools.lru_cache)
        signature = inspect.signature(subject)
    parameters = list(signature.parameters.values())
    return_annotation = signature.return_annotation

    try:
        # Resolve annotations using ``get_type_hints()`` and type_aliases.
        localns = TypeAliasNamespace(type_aliases)
        annotations = typing.get_type_hints(subject, None, localns)
        for i, param in enumerate(parameters):
            if param.name in annotations:
                annotation = annotations[param.name]
                if isinstance(annotation, TypeAliasForwardRef):
                    annotation = annotation.name
                parameters[i] = param.replace(annotation=annotation)
        if 'return' in annotations:
            if isinstance(annotations['return'], TypeAliasForwardRef):
                return_annotation = annotations['return'].name
            else:
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
    return inspect.Signature(
        parameters, return_annotation=return_annotation, __validate_parameters__=False
    )


def evaluate_signature(
    sig: inspect.Signature,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
) -> inspect.Signature:
    """Evaluate unresolved type annotations in a signature object."""

    def evaluate_forwardref(
        ref: ForwardRef,
        globalns: dict[str, Any] | None,
        localns: dict[str, Any] | None,
    ) -> Any:
        """Evaluate a forward reference."""
        return ref._evaluate(globalns, localns, frozenset())

    def evaluate(
        annotation: Any,
        globalns: dict[str, Any],
        localns: dict[str, Any],
    ) -> Any:
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


def stringify_signature(
    sig: inspect.Signature,
    show_annotation: bool = True,
    show_return_annotation: bool = True,
    unqualified_typehints: bool = False,
) -> str:
    """Stringify a Signature object.

    :param show_annotation: If enabled, show annotations on the signature
    :param show_return_annotation: If enabled, show annotation of the return value
    :param unqualified_typehints: If enabled, show annotations as unqualified
                                  (ex. io.StringIO -> StringIO)
    """
    if unqualified_typehints:
        mode = 'smart'
    else:
        mode = 'fully-qualified'

    EMPTY = Parameter.empty

    args = []
    last_kind = None
    for param in sig.parameters.values():
        if param.kind != Parameter.POSITIONAL_ONLY and last_kind == Parameter.POSITIONAL_ONLY:
            # PEP-570: Separator for Positional Only Parameter: /
            args.append('/')
        if param.kind == Parameter.KEYWORD_ONLY and last_kind in (
            Parameter.POSITIONAL_OR_KEYWORD,
            Parameter.POSITIONAL_ONLY,
            None,
        ):
            # PEP-3102: Separator for Keyword Only Parameter: *
            args.append('*')

        arg = StringIO()
        if param.kind is Parameter.VAR_POSITIONAL:
            arg.write('*' + param.name)
        elif param.kind is Parameter.VAR_KEYWORD:
            arg.write('**' + param.name)
        else:
            arg.write(param.name)

        if show_annotation and param.annotation is not EMPTY:
            arg.write(': ')
            arg.write(stringify_annotation(param.annotation, mode))
        if param.default is not EMPTY:
            if show_annotation and param.annotation is not EMPTY:
                arg.write(' = ')
            else:
                arg.write('=')
            arg.write(object_description(param.default))

        args.append(arg.getvalue())
        last_kind = param.kind

    if last_kind is Parameter.POSITIONAL_ONLY:
        # PEP-570: Separator for Positional Only Parameter: /
        args.append('/')

    concatenated_args = ', '.join(args)
    if sig.return_annotation is EMPTY or not show_annotation or not show_return_annotation:
        return f'({concatenated_args})'
    else:
        annotation = stringify_annotation(sig.return_annotation, mode)
        return f'({concatenated_args}) -> {annotation}'


def signature_from_str(signature: str) -> inspect.Signature:
    """Create a Signature object from string."""
    code = 'def func' + signature + ': pass'
    module = ast.parse(code)
    function = typing.cast(ast.FunctionDef, module.body[0])

    return signature_from_ast(function, code)


def signature_from_ast(node: ast.FunctionDef, code: str = '') -> inspect.Signature:
    """Create a Signature object from AST *node*."""
    EMPTY: type[Any] = Parameter.empty

    args: ast.arguments = node.args
    default_expressions: tuple[ast.expr | None, ...] = tuple(args.defaults)
    pos_only_offset = len(args.posonlyargs)
    defaults_offset = pos_only_offset + len(args.args) - len(args.defaults)
    # The sequence ``D = args.defaults`` contains non-None AST expressions,
    # so we can use ``None`` as a sentinel value for that to indicate that
    # there is no default value for a specific parameter.
    #
    # Let *p* be the number of positional-only and positional-or-keyword
    # arguments. Note that ``0 <= len(D) <= p`` and ``D[0]`` is the default
    # value corresponding to a positional-only *or* a positional-or-keyword
    # argument. Since a non-default argument cannot follow a default argument,
    # the sequence *D* can be completed on the left by adding None sentinels
    # so that ``len(D) == p`` and ``D[i]`` is the *i*-th default argument.
    default_expressions = (None,) * defaults_offset + default_expressions

    # construct the parameters list
    params: list[Parameter] = []

    # The real type of a parameter's kind is ``inspect._ParameterKind``
    # but this (integral) enumeration is not part of the public API.
    def process_arg(kind: Any, arg: ast.arg, *, defexpr: ast.expr | None = None) -> None:
        default: Any = EMPTY if defexpr is None else DefaultValue(ast_unparse(defexpr, code))
        annotation = ast_unparse(arg.annotation, code) or EMPTY
        params.append(Parameter(arg.arg, kind, default=default, annotation=annotation))

    # positional-only arguments (introduced in Python 3.8)
    for arg, defexpr in zip(args.posonlyargs, default_expressions):
        process_arg(Parameter.POSITIONAL_ONLY, arg, defexpr=defexpr)

    # normal arguments
    for arg, defexpr in zip(args.args, default_expressions[pos_only_offset:]):
        process_arg(Parameter.POSITIONAL_OR_KEYWORD, arg, defexpr=defexpr)

    # variadic positional argument (no possible default expression)
    if args.vararg:
        process_arg(Parameter.VAR_POSITIONAL, args.vararg, defexpr=None)

    # keyword-only arguments
    for arg, defexpr in zip(args.kwonlyargs, args.kw_defaults):
        process_arg(Parameter.KEYWORD_ONLY, arg, defexpr=defexpr)

    # variadic keyword argument (no possible default expression)
    if args.kwarg:
        process_arg(Parameter.VAR_KEYWORD, args.kwarg, defexpr=None)

    return_annotation = ast_unparse(node.returns, code) or EMPTY

    return inspect.Signature(params, return_annotation=return_annotation)


def getdoc(
    obj: Any,
    attrgetter: Callable = safe_getattr,
    allow_inherited: bool = False,
    cls: Any = None,
    name: str | None = None,
) -> str | None:
    """Get the docstring for the object.

    This tries to obtain the docstring for some kind of objects additionally:

    * partial functions
    * inherited docstring
    * inherited decorated methods
    """

    def getdoc_internal(
        obj: Any, attrgetter: Callable[[Any, str, Any], Any] = safe_getattr
    ) -> str | None:
        doc = attrgetter(obj, '__doc__', None)
        if isinstance(doc, str):
            return doc
        return None

    if cls and name and isclassmethod(obj, cls, name):
        for basecls in getmro(cls):
            meth = basecls.__dict__.get(name)
            if meth and hasattr(meth, '__func__'):
                doc: str | None = getdoc(meth.__func__)
                if doc is not None or not allow_inherited:
                    return doc

    doc = getdoc_internal(obj)
    if ispartial(obj) and doc == obj.__class__.__doc__:
        return getdoc(obj.func)
    elif doc is None and allow_inherited:
        if cls and name:
            # Check a docstring of the attribute or method from super classes.
            for basecls in getmro(cls):
                meth = safe_getattr(basecls, name, None)
                if meth is not None:
                    doc = getdoc_internal(meth)
                    if doc is not None:
                        break

            if doc is None:
                # retry using `inspect.getdoc()`
                for basecls in getmro(cls):
                    meth = safe_getattr(basecls, name, None)
                    if meth is not None:
                        doc = inspect.getdoc(meth)
                        if doc is not None:
                            break

        if doc is None:
            doc = inspect.getdoc(obj)

    return doc
