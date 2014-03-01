# -*- coding: utf-8 -*-
"""
    sphinx.util.inspect
    ~~~~~~~~~~~~~~~~~~~

    Helpers for inspecting Python modules.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

# this imports the standard library inspect module without resorting to
# relatively import this module
inspect = __import__('inspect')

from sphinx.util import force_decode
from sphinx.util.pycompat import bytes, builtins


if sys.version_info >= (3, 0):
    from functools import partial
    def getargspec(func):
        """Like inspect.getargspec but supports functools.partial as well."""
        if inspect.ismethod(func):
            func = func.__func__
        if type(func) is partial:
            orig_func = func.func
            argspec = getargspec(orig_func)
            args = list(argspec[0])
            defaults = list(argspec[3] or ())
            kwoargs = list(argspec[4])
            kwodefs = dict(argspec[5] or {})
            if func.args:
                args = args[len(func.args):]
            for arg in func.keywords or ():
                try:
                    i = args.index(arg) - len(args)
                    del args[i]
                    try:
                        del defaults[i]
                    except IndexError:
                        pass
                except ValueError:   # must be a kwonly arg
                    i = kwoargs.index(arg)
                    del kwoargs[i]
                    del kwodefs[arg]
            return inspect.FullArgSpec(args, argspec[1], argspec[2],
                                       tuple(defaults), kwoargs,
                                       kwodefs, argspec[6])
        while hasattr(func, '__wrapped__'):
            func = func.__wrapped__
        if not inspect.isfunction(func):
            raise TypeError('%r is not a Python function' % func)
        return inspect.getfullargspec(func)

elif sys.version_info >= (2, 5):
    from functools import partial
    def getargspec(func):
        """Like inspect.getargspec but supports functools.partial as well."""
        if inspect.ismethod(func):
            func = func.im_func
        parts = 0, ()
        if type(func) is partial:
            keywords = func.keywords
            if keywords is None:
                keywords = {}
            parts = len(func.args), keywords.keys()
            func = func.func
        if not inspect.isfunction(func):
            raise TypeError('%r is not a Python function' % func)
        args, varargs, varkw = inspect.getargs(func.func_code)
        func_defaults = func.func_defaults
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
        if sys.version_info >= (2, 6):
            return inspect.ArgSpec(args, varargs, varkw, func_defaults)
        else:
            return (args, varargs, varkw, func_defaults)
else:
    getargspec = inspect.getargspec


def isdescriptor(x):
    """Check if the object is some kind of descriptor."""
    for item in '__get__', '__set__', '__delete__':
        if hasattr(safe_getattr(x, item, None), '__call__'):
            return True
    return False


def safe_getattr(obj, name, *defargs):
    """A getattr() that turns all exceptions into AttributeErrors."""
    try:
        return getattr(obj, name, *defargs)
    except Exception:
        # this is a catch-all for all the weird things that some modules do
        # with attribute access
        if defargs:
            return defargs[0]
        raise AttributeError(name)


def safe_getmembers(object, predicate=None, attr_getter=safe_getattr):
    """A version of inspect.getmembers() that uses safe_getattr()."""
    results = []
    for key in dir(object):
        try:
            value = attr_getter(object, key, None)
        except AttributeError:
            continue
        if not predicate or predicate(value):
            results.append((key, value))
    results.sort()
    return results


def safe_repr(object):
    """A repr() implementation that returns text safe to use in reST context."""
    try:
        s = repr(object)
    except Exception:
        raise ValueError
    if isinstance(s, bytes):
        return force_decode(s, None).replace('\n', ' ')
    return s.replace('\n', ' ')


def is_builtin_class_method(obj, attr_name):
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
