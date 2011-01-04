# -*- coding: utf-8 -*-
"""
    sphinx.util.jsonimpl
    ~~~~~~~~~~~~~~~~~~~~

    JSON serializer implementation wrapper.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import UserString

try:
    import json
    # json-py's json module has no JSONEncoder; this will raise AttributeError
    # if json-py is imported instead of the built-in json module
    JSONEncoder = json.JSONEncoder
except (ImportError, AttributeError):
    try:
        import simplejson as json
        JSONEncoder = json.JSONEncoder
    except ImportError:
        json = None
        JSONEncoder = object


class SphinxJSONEncoder(JSONEncoder):
    """JSONEncoder subclass that forces translation proxies."""
    def default(self, obj):
        if isinstance(obj, UserString.UserString):
            return unicode(obj)
        return JSONEncoder.default(self, obj)


def dump(obj, fp, *args, **kwds):
    kwds['cls'] = SphinxJSONEncoder
    return json.dump(obj, fp, *args, **kwds)

def dumps(obj, *args, **kwds):
    kwds['cls'] = SphinxJSONEncoder
    return json.dumps(obj, *args, **kwds)

def load(*args, **kwds):
    return json.load(*args, **kwds)

def loads(*args, **kwds):
    return json.loads(*args, **kwds)
