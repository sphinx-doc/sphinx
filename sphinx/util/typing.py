"""The composite types for Sphinx."""

from __future__ import annotations

import sys
import typing
from struct import Struct
from types import TracebackType
from typing import Any, Callable, Dict, ForwardRef, List, Tuple, TypeVar, Union

from docutils import nodes
from docutils.parsers.rst.states import Inliner

try:
    from types import UnionType  # type: ignore  # python 3.10 or above
except ImportError:
    UnionType = None

# builtin classes that have incorrect __module__
INVALID_BUILTIN_CLASSES = {
    Struct: 'struct.Struct',  # Before Python 3.9
    TracebackType: 'types.TracebackType',
}


def is_invalid_builtin_class(obj: Any) -> bool:
    """Check *obj* is an invalid built-in class."""
    try:
        return obj in INVALID_BUILTIN_CLASSES
    except TypeError:  # unhashable type
        return False


# Text like nodes which are initialized with text and rawsource
TextlikeNode = Union[nodes.Text, nodes.TextElement]

# type of None
NoneType = type(None)

# path matcher
PathMatcher = Callable[[str], bool]

# common role functions
RoleFunction = Callable[[str, str, str, int, Inliner, Dict[str, Any], List[str]],
                        Tuple[List[nodes.Node], List[nodes.system_message]]]

# A option spec for directive
OptionSpec = Dict[str, Callable[[str], Any]]

# title getter functions for enumerable nodes (see sphinx.domains.std)
TitleGetter = Callable[[nodes.Node], str]

# inventory data on memory
InventoryItem = Tuple[
    str,  # project name
    str,  # project version
    str,  # URL
    str,  # display name
]
Inventory = Dict[str, Dict[str, InventoryItem]]


def get_type_hints(
    obj: Any, globalns: dict[str, Any] | None = None, localns: dict | None = None,
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
        # Invalid object is given. But try to get __annotations__ as a fallback for
        # the code using type union operator (PEP 604) in python 3.9 or below.
        return safe_getattr(obj, '__annotations__', {})
    except KeyError:
        # a broken class found (refs: https://github.com/sphinx-doc/sphinx/issues/8084)
        return {}


def is_system_TypeVar(typ: Any) -> bool:
    """Check *typ* is system defined TypeVar."""
    modname = getattr(typ, '__module__', '')
    return modname == 'typing' and isinstance(typ, TypeVar)


def restify(cls: type | None, mode: str = 'fully-qualified-except-typing') -> str:
    """Convert python class to a reST reference.

    :param mode: Specify a method how annotations will be stringified.

                 'fully-qualified-except-typing'
                     Show the module name and qualified name of the annotation except
                     the "typing" module.
                 'smart'
                     Show the name of the annotation.
    """
    from sphinx.ext.autodoc.mock import ismock, ismockmodule  # lazy loading
    from sphinx.util import inspect  # lazy loading

    if mode == 'smart':
        modprefix = '~'
    else:
        modprefix = ''

    try:
        if cls is None or cls is NoneType:
            return ':py:obj:`None`'
        elif cls is Ellipsis:
            return '...'
        elif isinstance(cls, str):
            return cls
        elif ismockmodule(cls):
            return f':py:class:`{modprefix}{cls.__name__}`'
        elif ismock(cls):
            return f':py:class:`{modprefix}{cls.__module__}.{cls.__name__}`'
        elif is_invalid_builtin_class(cls):
            return f':py:class:`{modprefix}{INVALID_BUILTIN_CLASSES[cls]}`'
        elif inspect.isNewType(cls):
            if sys.version_info[:2] >= (3, 10):
                # newtypes have correct module info since Python 3.10+
                return f':py:class:`{modprefix}{cls.__module__}.{cls.__name__}`'
            else:
                return ':py:class:`%s`' % cls.__name__
        elif UnionType and isinstance(cls, UnionType):
            if len(cls.__args__) > 1 and None in cls.__args__:
                args = ' | '.join(restify(a, mode) for a in cls.__args__ if a)
                return 'Optional[%s]' % args
            else:
                return ' | '.join(restify(a, mode) for a in cls.__args__)
        elif cls.__module__ in ('__builtin__', 'builtins'):
            if hasattr(cls, '__args__'):
                concatenated_args = ', '.join(restify(arg, mode) for arg in cls.__args__)
                return fr':py:class:`{cls.__name__}`\ [{concatenated_args}]'
            else:
                return ':py:class:`%s`' % cls.__name__
        elif (inspect.isgenericalias(cls)
              and cls.__module__ == 'typing'
              and cls.__origin__ is Union):  # type: ignore[attr-defined]
            if (len(cls.__args__) > 1  # type: ignore[attr-defined]
                    and cls.__args__[-1] is NoneType):  # type: ignore[attr-defined]
                if len(cls.__args__) > 2:  # type: ignore[attr-defined]
                    args = ', '.join(restify(a, mode)
                                     for a in cls.__args__[:-1])  # type: ignore[attr-defined]
                    return ':py:obj:`~typing.Optional`\\ [:obj:`~typing.Union`\\ [%s]]' % args
                else:
                    return ':py:obj:`~typing.Optional`\\ [%s]' % restify(
                        cls.__args__[0], mode)  # type: ignore[attr-defined]
            else:
                args = ', '.join(restify(a, mode)
                                 for a in cls.__args__)  # type: ignore[attr-defined]
                return ':py:obj:`~typing.Union`\\ [%s]' % args
        elif inspect.isgenericalias(cls):
            if isinstance(cls.__origin__, typing._SpecialForm):  # type: ignore[attr-defined]
                text = restify(cls.__origin__, mode)  # type: ignore
            elif getattr(cls, '_name', None):
                cls_name = cls._name  # type: ignore[attr-defined]
                if cls.__module__ == 'typing':
                    text = f':py:class:`~{cls.__module__}.{cls_name}`'
                else:
                    text = f':py:class:`{modprefix}{cls.__module__}.{cls_name}`'
            else:
                text = restify(cls.__origin__, mode)  # type: ignore[attr-defined]

            origin = getattr(cls, '__origin__', None)
            if not hasattr(cls, '__args__'):  # NoQA: SIM114
                pass
            elif all(is_system_TypeVar(a) for a in cls.__args__):
                # Suppress arguments if all system defined TypeVars (ex. Dict[KT, VT])
                pass
            elif (cls.__module__ == 'typing'
                  and cls._name == 'Callable'):  # type: ignore[attr-defined]
                args = ', '.join(restify(a, mode) for a in cls.__args__[:-1])
                text += fr"\ [[{args}], {restify(cls.__args__[-1], mode)}]"
            elif cls.__module__ == 'typing' and getattr(origin, '_name', None) == 'Literal':
                text += r"\ [%s]" % ', '.join(repr(a) for a in cls.__args__)
            elif cls.__args__:
                text += r"\ [%s]" % ", ".join(restify(a, mode) for a in cls.__args__)

            return text
        elif isinstance(cls, typing._SpecialForm):
            return f':py:obj:`~{cls.__module__}.{cls._name}`'  # type: ignore[attr-defined]
        elif sys.version_info[:2] >= (3, 11) and cls is typing.Any:
            # handle bpo-46998
            return f':py:obj:`~{cls.__module__}.{cls.__name__}`'
        elif hasattr(cls, '__qualname__'):
            if cls.__module__ == 'typing':
                return f':py:class:`~{cls.__module__}.{cls.__qualname__}`'
            else:
                return f':py:class:`{modprefix}{cls.__module__}.{cls.__qualname__}`'
        elif isinstance(cls, ForwardRef):
            return ':py:class:`%s`' % cls.__forward_arg__
        else:
            # not a class (ex. TypeVar)
            if cls.__module__ == 'typing':
                return f':py:obj:`~{cls.__module__}.{cls.__name__}`'
            else:
                return f':py:obj:`{modprefix}{cls.__module__}.{cls.__name__}`'
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
        raise ValueError("'mode' must be one of 'fully-qualified-except-typing', "
                         f"'fully-qualified', or 'smart'; got {mode!r}.")

    if mode == 'smart':
        module_prefix = '~'
    else:
        module_prefix = ''

    annotation_qualname = getattr(annotation, '__qualname__', '')
    annotation_module = getattr(annotation, '__module__', '')
    annotation_name = getattr(annotation, '__name__', '')
    annotation_module_is_typing = annotation_module == 'typing'

    if isinstance(annotation, str):
        if annotation.startswith("'") and annotation.endswith("'"):
            # might be a double Forward-ref'ed type.  Go unquoting.
            return annotation[1:-1]
        else:
            return annotation
    elif isinstance(annotation, TypeVar):
        if annotation_module_is_typing and mode in {'fully-qualified-except-typing', 'smart'}:
            return annotation_name
        else:
            return module_prefix + f'{annotation_module}.{annotation_name}'
    elif isNewType(annotation):
        if sys.version_info[:2] >= (3, 10):
            # newtypes have correct module info since Python 3.10+
            return module_prefix + f'{annotation_module}.{annotation_name}'
        else:
            return annotation_name
    elif not annotation:
        return repr(annotation)
    elif annotation is NoneType:
        return 'None'
    elif ismockmodule(annotation):
        return module_prefix + annotation_name
    elif ismock(annotation):
        return module_prefix + f'{annotation_module}.{annotation_name}'
    elif is_invalid_builtin_class(annotation):
        return module_prefix + INVALID_BUILTIN_CLASSES[annotation]
    elif str(annotation).startswith('typing.Annotated'):  # for py310+
        pass
    elif annotation_module == 'builtins' and annotation_qualname:
        if hasattr(annotation, '__args__'):  # PEP 585 generic
            return repr(annotation)
        else:
            return annotation_qualname
    elif annotation is Ellipsis:
        return '...'

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
            _name = getattr(annotation, '_name', '')
            if _name:
                qualname = _name
            elif annotation_qualname:
                qualname = annotation_qualname
            else:
                qualname = stringify_annotation(
                    annotation.__origin__, 'fully-qualified-except-typing',
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
            args = ', '.join(repr(a) for a in annotation_args)
            return f'{module_prefix}Literal[{args}]'
        elif str(annotation).startswith('typing.Annotated'):  # for py39+
            return stringify_annotation(annotation_args[0], mode)
        elif all(is_system_TypeVar(a) for a in annotation_args):
            # Suppress arguments if all system defined TypeVars (ex. Dict[KT, VT])
            return module_prefix + qualname
        else:
            args = ', '.join(stringify_annotation(a, mode) for a in annotation_args)
            return f'{module_prefix}{qualname}[{args}]'

    return module_prefix + qualname


# deprecated name -> (object to return, canonical path or empty string)
_DEPRECATED_OBJECTS = {
    'stringify': (stringify_annotation, 'sphinx.util.typing.stringify_annotation'),
}


def __getattr__(name):
    if name not in _DEPRECATED_OBJECTS:
        raise AttributeError(f'module {__name__!r} has no attribute {name!r}')

    from sphinx.deprecation import _deprecation_warning

    deprecated_object, canonical_name = _DEPRECATED_OBJECTS[name]
    _deprecation_warning(__name__, name, canonical_name, remove=(8, 0))
    return deprecated_object
