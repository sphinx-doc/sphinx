# -*- coding: utf-8 -*-
"""
    sphinx.util.inspect
    ~~~~~~~~~~~~~~~~~~~

    Helpers for inspecting Python modules.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

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
