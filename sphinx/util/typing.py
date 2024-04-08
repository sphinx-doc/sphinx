"""The composite types for Sphinx."""

from __future__ import annotations

import sys
import types
import typing
from collections.abc import Sequence
from contextvars import Context, ContextVar, Token
from struct import Struct
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ForwardRef,
    TypedDict,
    TypeVar,
    Union,
)

from docutils import nodes
from docutils.parsers.rst.states import Inliner

if TYPE_CHECKING:
    import enum
    from collections.abc import Mapping

    from typing_extensions import TypeGuard

    from sphinx.application import Sphinx

    class _SpecialForm(typing.Protocol):
        _name: str


if sys.version_info >= (3, 10):
    from types import UnionType
else:
    UnionType = None

# classes that have an incorrect .__module__ attribute
_INVALID_BUILTIN_CLASSES: Mapping[object, str] = {
    Context: 'contextvars.Context',  # Context.__module__ == '_contextvars'
    ContextVar: 'contextvars.ContextVar',  # ContextVar.__module__ == '_contextvars'
    Token: 'contextvars.Token',  # Token.__module__ == '_contextvars'
    Struct: 'struct.Struct',  # Struct.__module__ == '_struct'
    # types in 'types' with <type>.__module__ == 'builtins':
    types.AsyncGeneratorType: 'types.AsyncGeneratorType',
    types.BuiltinFunctionType: 'types.BuiltinFunctionType',
    types.BuiltinMethodType: 'types.BuiltinMethodType',
    types.CellType: 'types.CellType',
    types.ClassMethodDescriptorType: 'types.ClassMethodDescriptorType',
    types.CodeType: 'types.CodeType',
    types.CoroutineType: 'types.CoroutineType',
    types.FrameType: 'types.FrameType',
    types.FunctionType: 'types.FunctionType',
    types.GeneratorType: 'types.GeneratorType',
    types.GetSetDescriptorType: 'types.GetSetDescriptorType',
    types.LambdaType: 'types.LambdaType',
    types.MappingProxyType: 'types.MappingProxyType',
    types.MemberDescriptorType: 'types.MemberDescriptorType',
    types.MethodDescriptorType: 'types.MethodDescriptorType',
    types.MethodType: 'types.MethodType',
    types.MethodWrapperType: 'types.MethodWrapperType',
    types.ModuleType: 'types.ModuleType',
    types.TracebackType: 'types.TracebackType',
    types.WrapperDescriptorType: 'types.WrapperDescriptorType',
}


def is_invalid_builtin_class(obj: Any) -> bool:
    """Check *obj* is an invalid built-in class."""
    try:
        return obj in _INVALID_BUILTIN_CLASSES
    except TypeError:  # unhashable type
        return False


# Text like nodes which are initialized with text and rawsource
TextlikeNode = Union[nodes.Text, nodes.TextElement]

# type of None
NoneType = type(None)

# path matcher
PathMatcher = Callable[[str], bool]

# common role functions
RoleFunction = Callable[
    [str, str, str, int, Inliner, dict[str, Any], Sequence[str]],
    tuple[list[nodes.Node], list[nodes.system_message]],
]

# A option spec for directive
OptionSpec = dict[str, Callable[[str], Any]]

# title getter functions for enumerable nodes (see sphinx.domains.std)
TitleGetter = Callable[[nodes.Node], str]

# inventory data on memory
InventoryItem = tuple[
    str,  # project name
    str,  # project version
    str,  # URL
    str,  # display name
]
Inventory = dict[str, dict[str, InventoryItem]]


class ExtensionMetadata(TypedDict, total=False):
    """The metadata returned by an extension's ``setup()`` function.

    See :ref:`ext-metadata`.
    """

    version: str
    """The extension version (default: ``'unknown version'``)."""
    env_version: int
    """An integer that identifies the version of env data added by the extension."""
    parallel_read_safe: bool
    """Indicate whether parallel reading of source files is supported
    by the extension.
    """
    parallel_write_safe: bool
    """Indicate whether parallel writing of output files is supported
    by the extension (default: ``True``).
    """


if TYPE_CHECKING:
    _ExtensionSetupFunc = Callable[[Sphinx], ExtensionMetadata]


def get_type_hints(
    obj: Any,
    globalns: dict[str, Any] | None = None,
    localns: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a dictionary containing type hints for a function, method, module or class
    object.

    This is a simple wrapper of `typing.get_type_hints()` that does not raise an error on
    runtime.
    """
    from sphinx.util.inspect import safe_getattr  # lazy loading

    try:
        return typing.get_type_hints(obj, globalns, localns)
    except NameError:
        # Failed to evaluate ForwardRef (maybe TYPE_CHECKING)
        return safe_getattr(obj, '__annotations__', {})
    except AttributeError:
        # Failed to evaluate ForwardRef (maybe not runtime checkable)
        return safe_getattr(obj, '__annotations__', {})
    except TypeError:
        # Invalid object is given. But try to get __annotations__ as a fallback.
        return safe_getattr(obj, '__annotations__', {})
    except KeyError:
        # a broken class found (refs: https://github.com/sphinx-doc/sphinx/issues/8084)
        return {}


def is_system_TypeVar(typ: Any) -> bool:
    """Check *typ* is system defined TypeVar."""
    modname = getattr(typ, '__module__', '')
    return modname == 'typing' and isinstance(typ, TypeVar)


def _is_special_form(obj: Any) -> TypeGuard[_SpecialForm]:
    return isinstance(obj, typing._SpecialForm)


def _is_annotated_form(obj: Any) -> TypeGuard[Annotated[Any, ...]]:
    return typing.get_origin(obj) is Annotated or str(obj) == 'typing.Annotated'


def _get_typing_internal_name(obj: Any) -> str | None:
    return getattr(obj, '_name', None)


def restify(cls: Any, mode: str = 'fully-qualified-except-typing') -> str:
    """Convert a python type-like object to a reST reference.

    :param mode: Specify a method how annotations will be stringified.

                 'fully-qualified-except-typing'
                     Show the module name and qualified name of the annotation except
                     the "typing" module.
                 'smart'
                     Show the name of the annotation.
    """
    from sphinx.ext.autodoc.mock import ismock, ismockmodule  # lazy loading
    from sphinx.util import inspect  # lazy loading

    if cls is None or cls is NoneType:
        return ':py:obj:`None`'

    if cls is Ellipsis:
        return '...'

    if isinstance(cls, str):
        return cls

    if mode == 'smart':
        modprefix = '~'
    else:
        modprefix = ''

    # NOTE: if more cases must be added, carefully check that they are placed
    #       correctly, i.e., check that the cases are from the most precise to
    #       the least precise case.

    try:
        if ismockmodule(cls):
            return f':py:class:`{modprefix}{cls.__name__}`'
        elif ismock(cls):
            return f':py:class:`{modprefix}{cls.__module__}.{cls.__name__}`'
        elif is_invalid_builtin_class(cls):  # this never raises TypeError
            return f':py:class:`{modprefix}{_INVALID_BUILTIN_CLASSES[cls]}`'
        elif inspect.isNewType(cls):
            if sys.version_info[:2] >= (3, 10):
                # newtypes have correct module info since Python 3.10+
                return f':py:class:`{modprefix}{cls.__module__}.{cls.__name__}`'
            return f':py:class:`{cls.__name__}`'
        elif UnionType and isinstance(cls, UnionType):
            return ' | '.join(restify(a, mode) for a in cls.__args__)
        elif cls.__module__ in ('__builtin__', 'builtins'):
            if hasattr(cls, '__args__'):
                __args__: tuple[Any, ...] = cls.__args__
                if not cls.__args__:  # Empty tuple, list, ...
                    return rf':py:class:`{cls.__name__}`\ [{__args__!r}]'

                concatenated_args = ', '.join(restify(arg, mode) for arg in __args__)
                return rf':py:class:`{cls.__name__}`\ [{concatenated_args}]'
            return f':py:class:`{cls.__name__}`'
        elif (
            inspect.isgenericalias(cls)
            and cls.__module__ == 'typing'
            and cls.__origin__ is Union
        ):
            # *cls* is defined in ``typing``, and thus ``__args__`` must exist
            if NoneType in (__args__ := cls.__args__):
                # Union[T_1, ..., T_k, None, T_{k+1}, ..., T_n]
                non_none = [a for a in __args__ if a is not NoneType]
                if len(non_none) == 1:
                    return rf':py:obj:`~typing.Optional`\ [{restify(non_none[0], mode)}]'
                args = ', '.join(restify(a, mode) for a in non_none)
                return rf':py:obj:`~typing.Optional`\ [:obj:`~typing.Union`\ [{args}]]'

            args = ', '.join(restify(a, mode) for a in __args__)
            return rf':py:obj:`~typing.Union`\ [{args}]'
        elif inspect.isgenericalias(cls):
            # A generic alias always has an __origin__, but it is difficult to
            # use a type guard on inspect.isgenericalias() (ideally, we would
            # like to use ``TypeIs`` introduced in Python 3.13+).
            if _is_special_form(__origin__ := cls.__origin__):
                text = restify(__origin__, mode)
            elif internal_name := _get_typing_internal_name(cls):
                prefix = '~' if cls.__module__ == 'typing' else modprefix
                text = f':py:class:`{prefix}{cls.__module__}.{internal_name}`'
            else:
                text = restify(__origin__, mode)

            if not (__args__ := getattr(cls, '__args__', ())):
                return text

            if all(map(is_system_TypeVar, __args__)):
                # do not print the arguments they are all type variables
                return text

            params: str | None = None

            if cls.__module__ == 'typing':
                if _get_typing_internal_name(cls) == 'Callable':
                    vargs = ', '.join(restify(a, mode) for a in __args__[:-1])
                    rtype = restify(__args__[-1], mode)
                    params = f'[{vargs}], {rtype}'
                elif _get_typing_internal_name(__origin__) == 'Literal':
                    literal_args = []
                    for a in __args__:
                        if inspect.isenumattribute(a):
                            literal_args.append(_format_literal_enum_arg(a, mode=mode))
                        else:
                            literal_args.append(repr(a))
                    params = ', '.join(literal_args)

            if params is None:
                # generic representation of the parameters
                params = ', '.join(restify(a, mode) for a in __args__)

            return rf'{text}\ [{params}]'
        elif _is_special_form(cls):
            return f':py:obj:`~{cls.__module__}.{cls._name}`'
        elif sys.version_info[:2] >= (3, 11) and cls is typing.Any:
            # handle bpo-46998
            return f':py:obj:`~{cls.__module__}.{cls.__name__}`'
        elif hasattr(cls, '__qualname__'):
            prefix = '~' if cls.__module__ == 'typing' else modprefix
            return f':py:class:`{prefix}{cls.__module__}.{cls.__qualname__}`'
        elif isinstance(cls, ForwardRef):
            return f':py:class:`{cls.__forward_arg__}`'
        else:
            # not a class (ex. TypeVar) but should have a __name__
            prefix = '~' if cls.__module__ == 'typing' else modprefix
            return f':py:obj:`{prefix}{cls.__module__}.{cls.__name__}`'
    except (AttributeError, TypeError):
        return inspect.object_description(cls)


def stringify_annotation(
    annotation: Any,
    /,
    mode: str = 'fully-qualified-except-typing',
) -> str:
    """Stringify type annotation object.

    :param annotation: The annotation to stringified.
    :param mode: Specify a method how annotations will be stringified.

                 'fully-qualified-except-typing'
                     Show the module name and qualified name of the annotation except
                     the "typing" module.
                 'smart'
                     Show the name of the annotation.
                 'fully-qualified'
                     Show the module name and qualified name of the annotation.
    """
    from sphinx.ext.autodoc.mock import ismock, ismockmodule  # lazy loading
    from sphinx.util.inspect import isNewType  # lazy loading

    if mode not in {'fully-qualified-except-typing', 'fully-qualified', 'smart'}:
        msg = (
            "'mode' must be one of 'fully-qualified-except-typing', "
            f"'fully-qualified', or 'smart'; got {mode!r}."
        )
        raise ValueError(msg)

    if isinstance(annotation, str):
        if annotation.startswith("'") and annotation.endswith("'"):
            # might be a double Forward-ref'ed type.  Go unquoting.
            return annotation[1:-1]
        return annotation

    # literal annotations
    if not annotation:
        return repr(annotation)
    elif annotation is NoneType:
        return 'None'
    elif annotation is Ellipsis:
        return '...'

    if mode == 'smart':
        module_prefix = '~'
    else:
        module_prefix = ''

    annotation_qualname = getattr(annotation, '__qualname__', '')
    annotation_module = getattr(annotation, '__module__', '')
    annotation_name = getattr(annotation, '__name__', '')
    annotation_module_is_typing = annotation_module == 'typing'

    # extract the annotation's base type by considering some special cases
    # that can be formatted directly

    if isinstance(annotation, TypeVar):
        if annotation_module_is_typing and mode in {'fully-qualified-except-typing', 'smart'}:
            return annotation_name
        return f'{module_prefix}{annotation_module}.{annotation_name}'
    elif isNewType(annotation):
        if sys.version_info[:2] >= (3, 10):
            # newtypes have correct module info since Python 3.10+
            return f'{module_prefix}{annotation_module}.{annotation_name}'
        return annotation_name
    # mock annotations
    elif ismockmodule(annotation):
        return module_prefix + annotation_name
    elif ismock(annotation):
        return module_prefix + f'{annotation_module}.{annotation_name}'
    elif is_invalid_builtin_class(annotation):
        return module_prefix + _INVALID_BUILTIN_CLASSES[annotation]
    # special cases
    elif _is_annotated_form(annotation):  # for py39+
        pass
    elif annotation_module == 'builtins' and annotation_qualname:
        if (args := getattr(annotation, '__args__', None)) is None:
            return annotation_qualname

        # PEP 585 generic
        if not args:  # Empty tuple, list, ...
            return repr(annotation)

        concatenated_args = ', '.join(stringify_annotation(arg, mode) for arg in args)
        return f'{annotation_qualname}[{concatenated_args}]'
    else:
        # add other special cases here
        pass

    module_prefix = f'{annotation_module}.'
    annotation_forward_arg = getattr(annotation, '__forward_arg__', None)
    if annotation_qualname or (annotation_module_is_typing and not annotation_forward_arg):
        if mode == 'smart':
            module_prefix = '~' + module_prefix
        if annotation_module_is_typing and mode == 'fully-qualified-except-typing':
            module_prefix = ''
    else:
        module_prefix = ''

    if annotation_module_is_typing:
        if annotation_forward_arg:
            # handle ForwardRefs
            qualname = annotation_forward_arg
        else:
            if internal_name := _get_typing_internal_name(annotation):
                qualname = internal_name
            elif annotation_qualname:
                qualname = annotation_qualname
            else:
                # in this case, we know that the annotation is a member
                # of :mod:`typing` and all of them define ``__origin__``
                qualname = stringify_annotation(
                    annotation.__origin__, 'fully-qualified-except-typing'
                ).replace('typing.', '')  # ex. Union
    elif annotation_qualname:
        qualname = annotation_qualname
    elif hasattr(annotation, '__origin__'):
        # instantiated generic provided by a user
        qualname = stringify_annotation(annotation.__origin__, mode)
    elif UnionType and isinstance(annotation, UnionType):  # types.UnionType (for py3.10+)
        qualname = 'types.UnionType'
    else:
        # we weren't able to extract the base type, appending arguments would
        # only make them appear twice
        return repr(annotation)

    # process the argument's part

    annotation_args = getattr(annotation, '__args__', None)
    if annotation_args:
        if not isinstance(annotation_args, (list, tuple)):
            # broken __args__ found
            pass
        elif qualname in {'Optional', 'Union', 'types.UnionType'}:
            return ' | '.join(stringify_annotation(a, mode) for a in annotation_args)
        elif qualname == 'Callable':
            args = ', '.join(stringify_annotation(a, mode) for a in annotation_args[:-1])
            returns = stringify_annotation(annotation_args[-1], mode)
            return f'{module_prefix}Callable[[{args}], {returns}]'
        elif qualname == 'Literal':
            from sphinx.util.inspect import isenumattribute  # lazy loading

            def format_literal_arg(arg: Any) -> str:
                if isenumattribute(arg):
                    enumcls = arg.__class__

                    if mode == 'smart':
                        # MyEnum.member
                        return f'{enumcls.__qualname__}.{arg.name}'

                    # module.MyEnum.member
                    return f'{enumcls.__module__}.{enumcls.__qualname__}.{arg.name}'
                return repr(arg)

            args = ', '.join(map(format_literal_arg, annotation_args))
            return f'{module_prefix}Literal[{args}]'
        elif _is_annotated_form(annotation):  # for py39+
            return stringify_annotation(annotation_args[0], mode)
        elif all(is_system_TypeVar(a) for a in annotation_args):
            # Suppress arguments if all system defined TypeVars (ex. Dict[KT, VT])
            return module_prefix + qualname
        else:
            args = ', '.join(stringify_annotation(a, mode) for a in annotation_args)
            return f'{module_prefix}{qualname}[{args}]'

    return module_prefix + qualname


def _format_literal_enum_arg(arg: enum.Enum, /, *, mode: str) -> str:
    enum_cls = arg.__class__
    if mode == 'smart' or enum_cls.__module__ == 'typing':
        return f':py:attr:`~{enum_cls.__module__}.{enum_cls.__qualname__}.{arg.name}`'
    return f':py:attr:`{enum_cls.__module__}.{enum_cls.__qualname__}.{arg.name}`'


# deprecated name -> (object to return, canonical path or empty string, removal version)
_DEPRECATED_OBJECTS: dict[str, tuple[Any, str, tuple[int, int]]] = {
    'stringify': (stringify_annotation, 'sphinx.util.typing.stringify_annotation', (8, 0)),
}


def __getattr__(name: str) -> Any:
    if name not in _DEPRECATED_OBJECTS:
        msg = f'module {__name__!r} has no attribute {name!r}'
        raise AttributeError(msg)

    from sphinx.deprecation import _deprecation_warning

    deprecated_object, canonical_name, remove = _DEPRECATED_OBJECTS[name]
    _deprecation_warning(__name__, name, canonical_name, remove=remove)
    return deprecated_object
