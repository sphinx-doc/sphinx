# -*- coding: utf-8 -*-
"""
    sphinx.util.inspect
    ~~~~~~~~~~~~~~~~~~~

    Helpers for inspecting Python modules.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

# this imports the standard library inspect module without resorting to
# relatively import this module
inspect = __import__('inspect')

from sphinx.util import force_decode
from sphinx.util.pycompat import bytes


if sys.version_info >= (2, 5):
    from functools import partial
    def getargspec(func):
        """Like inspect.getargspec but supports functools.partial as well."""
        if inspect.ismethod(func):
            func = func.im_func
        parts = 0, ()
        if type(func) is partial:
            parts = len(func.args), func.keywords.keys()
            func = func.func
        if not inspect.isfunction(func):
            raise TypeError('%r is not a Python function' % func)
        args, varargs, varkw = inspect.getargs(func.func_code)
        func_defaults = func.func_defaults
        if func_defaults:
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


def safe_getmembers(object, predicate=None):
    """A version of inspect.getmembers() that uses safe_getattr()."""
    results = []
    for key in dir(object):
        try:
            value = safe_getattr(object, key, None)
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
