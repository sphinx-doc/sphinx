# -*- coding: utf-8 -*-
"""
    sphinx.util.inspect
    ~~~~~~~~~~~~~~~~~~~

    Helpers for inspecting Python modules.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import absolute_import

import re
import typing
import inspect
from collections import OrderedDict

from six import PY2, PY3, StringIO, binary_type, string_types, itervalues
from six.moves import builtins

from sphinx.util import force_decode

if False:
    # For type annotation
    from typing import Any, Callable, Dict, List, Tuple, Type  # NOQA

memory_address_re = re.compile(r' at 0x[0-9a-f]{8,16}(?=>)', re.IGNORECASE)


if PY3:
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
                    defaults += (param.default,)
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

else:  # 2.7
    from functools import partial

    def getargspec(func):
        # type: (Any) -> Any
        """Like inspect.getargspec but supports functools.partial as well."""
        if inspect.ismethod(func):
            func = func.__func__
        parts = 0, ()  # type: Tuple[int, Tuple[unicode, ...]]
        if type(func) is partial:
            keywords = func.keywords
            if keywords is None:
                keywords = {}
            parts = len(func.args), keywords.keys()
            func = func.func
        if not inspect.isfunction(func):
            raise TypeError('%r is not a Python function' % func)
        args, varargs, varkw = inspect.getargs(func.__code__)  # type: ignore
        func_defaults = func.__defaults__
        if func_defaults is None:
            func_defaults = []
        else:
            func_defaults = list(func_defaults)
        if parts[0]:
            args = args[parts[0]:]
        if parts[1]:
            for arg in parts[1]:
                i = args.index(arg) - len(args)
                del args[i]
                try:
                    del func_defaults[i]
                except IndexError:
                    pass
        return inspect.ArgSpec(args, varargs, varkw, func_defaults)

try:
    import enum
except ImportError:
    enum = None


def isenumclass(x):
    # type: (Type) -> bool
    """Check if the object is subclass of enum."""
    if enum is None:
        return False
    return inspect.isclass(x) and issubclass(x, enum.Enum)


def isenumattribute(x):
    # type: (Any) -> bool
    """Check if the object is attribute of enum."""
    if enum is None:
        return False
    return isinstance(x, enum.Enum)


def isdescriptor(x):
    # type: (Any) -> bool
    """Check if the object is some kind of descriptor."""
    for item in '__get__', '__set__', '__delete__':
        if hasattr(safe_getattr(x, item, None), '__call__'):
            return True
    return False


def safe_getattr(obj, name, *defargs):
    # type: (Any, unicode, unicode) -> object
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


def safe_getmembers(object, predicate=None, attr_getter=safe_getattr):
    # type: (Any, Callable[[unicode], bool], Callable) -> List[Tuple[unicode, Any]]
    """A version of inspect.getmembers() that uses safe_getattr()."""
    results = []  # type: List[Tuple[unicode, Any]]
    for key in dir(object):
        try:
            value = attr_getter(object, key, None)
        except AttributeError:
            continue
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results


def object_description(object):
    # type: (Any) -> unicode
    """A repr() implementation that returns text safe to use in reST context."""
    try:
        s = repr(object)
    except Exception:
        raise ValueError
    if isinstance(s, binary_type):
        s = force_decode(s, None)  # type: ignore
    # Strip non-deterministic memory addresses such as
    # ``<__main__.A at 0x7f68cb685710>``
    s = memory_address_re.sub('', s)
    return s.replace('\n', ' ')


def is_builtin_class_method(obj, attr_name):
    # type: (Any, unicode) -> bool
    """If attr_name is implemented at builtin class, return True.

        >>> is_builtin_class_method(int, '__init__')
        True

    Why this function needed? CPython implements int.__init__ by Descriptor
    but PyPy implements it by pure Python code.
    """
    classes = [c for c in inspect.getmro(obj) if attr_name in c.__dict__]
    cls = classes[0] if classes else object

    if not hasattr(builtins, safe_getattr(cls, '__name__', '')):  # type: ignore
        return False
    return getattr(builtins, safe_getattr(cls, '__name__', '')) is cls  # type: ignore


class Parameter(object):
    """Fake parameter class for python2."""
    POSITIONAL_ONLY = 0
    POSITIONAL_OR_KEYWORD = 1
    VAR_POSITIONAL = 2
    KEYWORD_ONLY = 3
    VAR_KEYWORD = 4
    empty = object()

    def __init__(self, name, kind=POSITIONAL_OR_KEYWORD, default=empty):
        # type: (str, int, Any) -> None
        self.name = name
        self.kind = kind
        self.default = default
        self.annotation = self.empty


class Signature(object):
    """The Signature object represents the call signature of a callable object and
    its return annotation.
    """

    def __init__(self, subject, bound_method=False):
        # type: (Callable, bool) -> None
        # check subject is not a built-in class (ex. int, str)
        if (isinstance(subject, type) and
                is_builtin_class_method(subject, "__new__") and
                is_builtin_class_method(subject, "__init__")):
            raise TypeError("can't compute signature for built-in type {}".format(subject))

        self.subject = subject

        if PY3:
            self.signatures = inspect.signature(subject)
        else:
            self.argspec = getargspec(subject)

        try:
            self.annotations = typing.get_type_hints(subject)
        except:
            self.annotations = None

        if bound_method:
            # client gives a hint that the subject is a bound method

            if PY3 and inspect.ismethod(subject):
                # inspect.signature already considers the subject is bound method.
                # So it is not need to skip first argument.
                self.skip_first_argument = False
            else:
                self.skip_first_argument = True
        else:
            if PY3:
                # inspect.signature recognizes type of method properly without any hints
                self.skip_first_argument = False
            else:
                # check the subject is bound method or not
                self.skip_first_argument = inspect.ismethod(subject) and subject.__self__  # type: ignore  # NOQA

    @property
    def parameters(self):
        # type: () -> Dict
        if PY3:
            return self.signatures.parameters
        else:
            params = OrderedDict()  # type: Dict
            positionals = len(self.argspec.args) - len(self.argspec.defaults)
            for i, arg in enumerate(self.argspec.args):
                if i < positionals:
                    params[arg] = Parameter(arg)
                else:
                    default = self.argspec.defaults[i - positionals]
                    params[arg] = Parameter(arg, default=default)
            if self.argspec.varargs:
                params[self.argspec.varargs] = Parameter(self.argspec.varargs,
                                                         Parameter.VAR_POSITIONAL)
            if self.argspec.keywords:
                params[self.argspec.keywords] = Parameter(self.argspec.keywords,
                                                          Parameter.VAR_KEYWORD)
            return params

    @property
    def return_annotation(self):
        # type: () -> Any
        if PY3:
            return self.signatures.return_annotation
        else:
            return None

    def format_args(self):
        # type: () -> unicode
        args = []
        last_kind = None
        for i, param in enumerate(itervalues(self.parameters)):
            # skip first argument if subject is bound method
            if self.skip_first_argument and i == 0:
                continue

            arg = StringIO()

            # insert '*' between POSITIONAL args and KEYWORD_ONLY args::
            #     func(a, b, *, c, d):
            if param.kind == param.KEYWORD_ONLY and last_kind in (param.POSITIONAL_OR_KEYWORD,
                                                                  param.POSITIONAL_ONLY):
                args.append('*')

            if param.kind in (param.POSITIONAL_ONLY,
                              param.POSITIONAL_OR_KEYWORD,
                              param.KEYWORD_ONLY):
                arg.write(param.name)
                if param.annotation is not param.empty:
                    if isinstance(param.annotation, string_types) and \
                            param.name in self.annotations:
                        arg.write(': ')
                        arg.write(self.format_annotation(self.annotations[param.name]))
                    else:
                        arg.write(': ')
                        arg.write(self.format_annotation(param.annotation))
                if param.default is not param.empty:
                    if param.annotation is param.empty:
                        arg.write('=')
                        arg.write(object_description(param.default))  # type: ignore
                    else:
                        arg.write(' = ')
                        arg.write(object_description(param.default))  # type: ignore
            elif param.kind == param.VAR_POSITIONAL:
                arg.write('*')
                arg.write(param.name)
            elif param.kind == param.VAR_KEYWORD:
                arg.write('**')
                arg.write(param.name)

            args.append(arg.getvalue())
            last_kind = param.kind

        if PY2 or self.return_annotation is inspect.Parameter.empty:
            return '(%s)' % ', '.join(args)
        else:
            if isinstance(self.return_annotation, string_types) and \
                    'return' in self.annotations:
                annotation = self.format_annotation(self.annotations['return'])
            else:
                annotation = self.format_annotation(self.return_annotation)

            return '(%s) -> %s' % (', '.join(args), annotation)

    def format_annotation(self, annotation):
        # type: (Any) -> str
        """Return formatted representation of a type annotation.

        Show qualified names for types and additional details for types from
        the ``typing`` module.

        Displaying complex types from ``typing`` relies on its private API.
        """
        if isinstance(annotation, string_types):
            return annotation  # type: ignore
        if isinstance(annotation, typing.TypeVar):  # type: ignore
            return annotation.__name__
        if annotation == Ellipsis:
            return '...'
        if not isinstance(annotation, type):
            return repr(annotation)

        qualified_name = (annotation.__module__ + '.' + annotation.__qualname__  # type: ignore
                          if annotation else repr(annotation))

        if annotation.__module__ == 'builtins':
            return annotation.__qualname__  # type: ignore
        elif isinstance(annotation, typing.GenericMeta):
            # In Python 3.5.2+, all arguments are stored in __args__,
            # whereas __parameters__ only contains generic parameters.
            #
            # Prior to Python 3.5.2, __args__ is not available, and all
            # arguments are in __parameters__.
            params = None
            if hasattr(annotation, '__args__'):
                if annotation.__args__ is None or len(annotation.__args__) <= 2:  # type: ignore  # NOQA
                    params = annotation.__args__  # type: ignore
                else:  # typing.Callable
                    args = ', '.join(self.format_annotation(arg) for arg
                                     in annotation.__args__[:-1])  # type: ignore
                    result = self.format_annotation(annotation.__args__[-1])  # type: ignore
                    return '%s[[%s], %s]' % (qualified_name, args, result)
            elif hasattr(annotation, '__parameters__'):
                params = annotation.__parameters__  # type: ignore
            if params is not None:
                param_str = ', '.join(self.format_annotation(p) for p in params)
                return '%s[%s]' % (qualified_name, param_str)
        elif (isinstance(annotation, typing.UnionMeta) and  # type: ignore
              hasattr(annotation, '__union_params__')):
            params = annotation.__union_params__  # type: ignore
            if params is not None:
                param_str = ', '.join(self.format_annotation(p) for p in params)
                return '%s[%s]' % (qualified_name, param_str)
        elif (isinstance(annotation, typing.CallableMeta) and  # type: ignore
              getattr(annotation, '__args__', None) is not None and
              hasattr(annotation, '__result__')):
            # Skipped in the case of plain typing.Callable
            args = annotation.__args__  # type: ignore
            if args is None:
                return qualified_name
            elif args is Ellipsis:
                args_str = '...'
            else:
                formatted_args = (self.format_annotation(a) for a in args)
                args_str = '[%s]' % ', '.join(formatted_args)
            return '%s[%s, %s]' % (qualified_name,
                                   args_str,
                                   self.format_annotation(annotation.__result__))  # type: ignore  # NOQA
        elif (isinstance(annotation, typing.TupleMeta) and  # type: ignore
              hasattr(annotation, '__tuple_params__') and
              hasattr(annotation, '__tuple_use_ellipsis__')):
            params = annotation.__tuple_params__  # type: ignore
            if params is not None:
                param_strings = [self.format_annotation(p) for p in params]
                if annotation.__tuple_use_ellipsis__:  # type: ignore
                    param_strings.append('...')
                return '%s[%s]' % (qualified_name,
                                   ', '.join(param_strings))

        return qualified_name
