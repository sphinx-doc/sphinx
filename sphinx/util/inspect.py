"""
    sphinx.util.inspect
    ~~~~~~~~~~~~~~~~~~~

    Helpers for inspecting Python modules.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import builtins
import enum
import inspect
import re
import sys
import typing
import warnings
from functools import partial, partialmethod
from inspect import (  # NOQA
    isclass, ismethod, ismethoddescriptor, isroutine
)
from io import StringIO
from typing import Any, Callable, Mapping, List, Tuple

from sphinx.deprecation import RemovedInSphinx30Warning
from sphinx.util import logging
from sphinx.util.typing import NoneType

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
def getargspec(func):
    """Like inspect.getfullargspec but supports bound methods, and wrapped
    methods."""
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

        if kind is inspect.Parameter.POSITIONAL_ONLY:
            args.append(name)
        elif kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
            args.append(name)
            if param.default is not param.empty:
                defaults += (param.default,)  # type: ignore
        elif kind is inspect.Parameter.VAR_POSITIONAL:
            varargs = name
        elif kind is inspect.Parameter.KEYWORD_ONLY:
            kwonlyargs.append(name)
            if param.default is not param.empty:
                kwdefaults[name] = param.default
        elif kind is inspect.Parameter.VAR_KEYWORD:
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


def isenumclass(x: Any) -> bool:
    """Check if the object is subclass of enum."""
    return inspect.isclass(x) and issubclass(x, enum.Enum)


def isenumattribute(x: Any) -> bool:
    """Check if the object is attribute of enum."""
    return isinstance(x, enum.Enum)


def ispartial(obj: Any) -> bool:
    """Check if the object is partial."""
    return isinstance(obj, (partial, partialmethod))


def isclassmethod(obj: Any) -> bool:
    """Check if the object is classmethod."""
    if isinstance(obj, classmethod):
        return True
    elif inspect.ismethod(obj) and obj.__self__ is not None:
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


def isattributedescriptor(obj: Any) -> bool:
    """Check if the object is an attribute like descriptor."""
    if inspect.isdatadescriptor(object):
        # data descriptor is kind of attribute
        return True
    elif isdescriptor(obj):
        # non data descriptor
        if isfunction(obj) or isbuiltin(obj) or inspect.ismethod(obj):
            # attribute must not be either function, builtin and method
            return False
        elif inspect.isclass(obj):
            # attribute must not be a class
            return False
        elif isinstance(obj, (ClassMethodDescriptorType,
                              MethodDescriptorType,
                              WrapperDescriptorType)):
            # attribute must not be a method descriptor
            return False
        elif type(obj).__name__ == "instancemethod":
            # attribute must not be an instancemethod (C-API)
            return False
        else:
            return True
    else:
        return False


def isfunction(obj: Any) -> bool:
    """Check if the object is function."""
    return inspect.isfunction(obj) or ispartial(obj) and inspect.isfunction(obj.func)


def isbuiltin(obj: Any) -> bool:
    """Check if the object is builtin."""
    return inspect.isbuiltin(obj) or ispartial(obj) and inspect.isbuiltin(obj.func)


def iscoroutinefunction(obj: Any) -> bool:
    """Check if the object is coroutine-function."""
    if hasattr(obj, '__code__') and inspect.iscoroutinefunction(obj):
        # check obj.__code__ because iscoroutinefunction() crashes for custom method-like
        # objects (see https://github.com/sphinx-doc/sphinx/issues/6605)
        return True
    elif (ispartial(obj) and hasattr(obj.func, '__code__') and
          inspect.iscoroutinefunction(obj.func)):
        # partialed
        return True
    else:
        return False


def isproperty(obj: Any) -> bool:
    """Check if the object is property."""
    return isinstance(obj, property)


def safe_getattr(obj: Any, name: str, *defargs) -> Any:
    """A getattr() that turns all exceptions into AttributeErrors."""
    try:
        return getattr(obj, name, *defargs)
    except Exception:
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

        raise AttributeError(name)


def safe_getmembers(object: Any, predicate: Callable[[str], bool] = None,
                    attr_getter: Callable = safe_getattr) -> List[Tuple[str, Any]]:
    """A version of inspect.getmembers() that uses safe_getattr()."""
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
    except Exception:
        raise ValueError
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
    classes = [c for c in inspect.getmro(obj) if attr_name in c.__dict__]
    cls = classes[0] if classes else object

    if not hasattr(builtins, safe_getattr(cls, '__name__', '')):
        return False
    return getattr(builtins, safe_getattr(cls, '__name__', '')) is cls


class Parameter:
    """Fake parameter class for python2."""
    POSITIONAL_ONLY = 0
    POSITIONAL_OR_KEYWORD = 1
    VAR_POSITIONAL = 2
    KEYWORD_ONLY = 3
    VAR_KEYWORD = 4
    empty = object()

    def __init__(self, name: str, kind: int = POSITIONAL_OR_KEYWORD,
                 default: Any = empty) -> None:
        self.name = name
        self.kind = kind
        self.default = default
        self.annotation = self.empty

        warnings.warn('sphinx.util.inspect.Parameter is deprecated.',
                      RemovedInSphinx30Warning, stacklevel=2)


class Signature:
    """The Signature object represents the call signature of a callable object and
    its return annotation.
    """

    def __init__(self, subject: Callable, bound_method: bool = False,
                 has_retval: bool = True) -> None:
        # check subject is not a built-in class (ex. int, str)
        if (isinstance(subject, type) and
                is_builtin_class_method(subject, "__new__") and
                is_builtin_class_method(subject, "__init__")):
            raise TypeError("can't compute signature for built-in type {}".format(subject))

        self.subject = subject
        self.has_retval = has_retval
        self.partialmethod_with_noargs = False

        try:
            self.signature = inspect.signature(subject)
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
                return inspect.Parameter.empty
        else:
            return None

    def format_args(self, show_annotation: bool = True) -> str:
        def format_param_annotation(param: inspect.Parameter) -> str:
            if isinstance(param.annotation, str) and param.name in self.annotations:
                return self.format_annotation(self.annotations[param.name])
            else:
                return self.format_annotation(param.annotation)

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
                    arg.write(format_param_annotation(param))
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
                    arg.write(format_param_annotation(param))
            elif param.kind == param.VAR_KEYWORD:
                arg.write('**')
                arg.write(param.name)
                if show_annotation and param.annotation is not param.empty:
                    arg.write(': ')
                    arg.write(format_param_annotation(param))

            args.append(arg.getvalue())
            last_kind = param.kind

        if self.return_annotation is inspect.Parameter.empty or show_annotation is False:
            return '(%s)' % ', '.join(args)
        else:
            if 'return' in self.annotations:
                annotation = self.format_annotation(self.annotations['return'])
            else:
                annotation = self.format_annotation(self.return_annotation)

            return '(%s) -> %s' % (', '.join(args), annotation)

    def format_annotation(self, annotation: Any) -> str:
        """Return formatted representation of a type annotation.

        Show qualified names for types and additional details for types from
        the ``typing`` module.

        Displaying complex types from ``typing`` relies on its private API.
        """
        if isinstance(annotation, str):
            return annotation
        elif isinstance(annotation, typing.TypeVar):  # type: ignore
            return annotation.__name__
        elif not annotation:
            return repr(annotation)
        elif annotation is NoneType:  # type: ignore
            return 'None'
        elif getattr(annotation, '__module__', None) == 'builtins':
            return annotation.__qualname__
        elif annotation is Ellipsis:
            return '...'

        if sys.version_info >= (3, 7):  # py37+
            return self.format_annotation_new(annotation)
        else:
            return self.format_annotation_old(annotation)

    def format_annotation_new(self, annotation: Any) -> str:
        """format_annotation() for py37+"""
        module = getattr(annotation, '__module__', None)
        if module == 'typing':
            if getattr(annotation, '_name', None):
                qualname = annotation._name
            elif getattr(annotation, '__qualname__', None):
                qualname = annotation.__qualname__
            elif getattr(annotation, '__forward_arg__', None):
                qualname = annotation.__forward_arg__
            else:
                qualname = self.format_annotation(annotation.__origin__)  # ex. Union
        elif hasattr(annotation, '__qualname__'):
            qualname = '%s.%s' % (module, annotation.__qualname__)
        else:
            qualname = repr(annotation)

        if getattr(annotation, '__args__', None):
            if qualname == 'Union':
                if len(annotation.__args__) == 2 and annotation.__args__[1] is NoneType:  # type: ignore  # NOQA
                    return 'Optional[%s]' % self.format_annotation(annotation.__args__[0])
                else:
                    args = ', '.join(self.format_annotation(a) for a in annotation.__args__)
                    return '%s[%s]' % (qualname, args)
            elif qualname == 'Callable':
                args = ', '.join(self.format_annotation(a) for a in annotation.__args__[:-1])
                returns = self.format_annotation(annotation.__args__[-1])
                return '%s[[%s], %s]' % (qualname, args, returns)
            elif annotation._special:
                return qualname
            else:
                args = ', '.join(self.format_annotation(a) for a in annotation.__args__)
                return '%s[%s]' % (qualname, args)

        return qualname

    def format_annotation_old(self, annotation: Any) -> str:
        """format_annotation() for py36 or below"""
        module = getattr(annotation, '__module__', None)
        if module == 'typing':
            if getattr(annotation, '_name', None):
                qualname = annotation._name
            elif getattr(annotation, '__qualname__', None):
                qualname = annotation.__qualname__
            elif getattr(annotation, '__forward_arg__', None):
                qualname = annotation.__forward_arg__
            elif getattr(annotation, '__origin__', None):
                qualname = self.format_annotation(annotation.__origin__)  # ex. Union
            else:
                qualname = repr(annotation).replace('typing.', '')
        elif hasattr(annotation, '__qualname__'):
            qualname = '%s.%s' % (module, annotation.__qualname__)
        else:
            qualname = repr(annotation)

        if (isinstance(annotation, typing.TupleMeta) and
                not hasattr(annotation, '__tuple_params__')):  # for Python 3.6
            params = annotation.__args__
            if params:
                param_str = ', '.join(self.format_annotation(p) for p in params)
                return '%s[%s]' % (qualname, param_str)
            else:
                return qualname
        elif isinstance(annotation, typing.GenericMeta):
            params = None
            if hasattr(annotation, '__args__'):
                # for Python 3.5.2+
                if annotation.__args__ is None or len(annotation.__args__) <= 2:  # type: ignore  # NOQA
                    params = annotation.__args__  # type: ignore
                else:  # typing.Callable
                    args = ', '.join(self.format_annotation(arg) for arg
                                     in annotation.__args__[:-1])  # type: ignore
                    result = self.format_annotation(annotation.__args__[-1])  # type: ignore
                    return '%s[[%s], %s]' % (qualname, args, result)
            elif hasattr(annotation, '__parameters__'):
                # for Python 3.5.0 and 3.5.1
                params = annotation.__parameters__  # type: ignore
            if params is not None:
                param_str = ', '.join(self.format_annotation(p) for p in params)
                return '%s[%s]' % (qualname, param_str)
        elif (hasattr(typing, 'UnionMeta') and
              isinstance(annotation, typing.UnionMeta) and
              hasattr(annotation, '__union_params__')):  # for Python 3.5
            params = annotation.__union_params__
            if params is not None:
                if len(params) == 2 and params[1] is NoneType:  # type: ignore
                    return 'Optional[%s]' % self.format_annotation(params[0])
                else:
                    param_str = ', '.join(self.format_annotation(p) for p in params)
                    return '%s[%s]' % (qualname, param_str)
        elif (hasattr(annotation, '__origin__') and
              annotation.__origin__ is typing.Union):  # for Python 3.5.2+
            params = annotation.__args__
            if params is not None:
                if len(params) == 2 and params[1] is NoneType:  # type: ignore
                    return 'Optional[%s]' % self.format_annotation(params[0])
                else:
                    param_str = ', '.join(self.format_annotation(p) for p in params)
                    return 'Union[%s]' % param_str
        elif (isinstance(annotation, typing.CallableMeta) and
              getattr(annotation, '__args__', None) is not None and
              hasattr(annotation, '__result__')):  # for Python 3.5
            # Skipped in the case of plain typing.Callable
            args = annotation.__args__
            if args is None:
                return qualname
            elif args is Ellipsis:
                args_str = '...'
            else:
                formatted_args = (self.format_annotation(a) for a in args)
                args_str = '[%s]' % ', '.join(formatted_args)
            return '%s[%s, %s]' % (qualname,
                                   args_str,
                                   self.format_annotation(annotation.__result__))
        elif (isinstance(annotation, typing.TupleMeta) and
              hasattr(annotation, '__tuple_params__') and
              hasattr(annotation, '__tuple_use_ellipsis__')):  # for Python 3.5
            params = annotation.__tuple_params__
            if params is not None:
                param_strings = [self.format_annotation(p) for p in params]
                if annotation.__tuple_use_ellipsis__:
                    param_strings.append('...')
                return '%s[%s]' % (qualname,
                                   ', '.join(param_strings))

        return qualname


def getdoc(obj: Any, attrgetter: Callable = safe_getattr,
           allow_inherited: bool = False) -> str:
    """Get the docstring for the object.

    This tries to obtain the docstring for some kind of objects additionally:

    * partial functions
    * inherited docstring
    """
    doc = attrgetter(obj, '__doc__', None)
    if ispartial(obj) and doc == obj.__class__.__doc__:
        return getdoc(obj.func)
    elif doc is None and allow_inherited:
        doc = inspect.getdoc(obj)

    return doc
