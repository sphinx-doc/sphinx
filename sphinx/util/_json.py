# -*- coding: utf-8 -*-
"""
    sphinx.util._json
    ~~~~~~~~~~~~~~~~~

    This module implements a simple JSON serializer if simplejson is
    unavailable.

    This is not fully JSON compliant but enough for the searchindex.
    And the generated files are smaller than the simplejson ones.

    Uses the basestring encode function from simplejson.

    :copyright: Copyright 2008 by Armin Ronacher, Bob Ippolito.
    :license: BSD.
"""
import re


# escape \, ", control characters and everything outside ASCII
ESCAPE_ASCII = re.compile(r'([\\"]|[^\ -~])')
ESCAPE_DICT = {
    '\\': '\\\\',
    '"': '\\"',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
}


def encode_basestring_ascii(s):
    def replace(match):
        s = match.group(0)
        try:
            return ESCAPE_DICT[s]
        except KeyError:
            n = ord(s)
            if n < 0x10000:
                return '\\u%04x' % (n,)
            else:
                # surrogate pair
                n -= 0x10000
                s1 = 0xd800 | ((n >> 10) & 0x3ff)
                s2 = 0xdc00 | (n & 0x3ff)
                return '\\u%04x\\u%04x' % (s1, s2)
    return '"' + str(ESCAPE_ASCII.sub(replace, s)) + '"'


def dumps(obj, key=False):
    if key:
        if not isinstance(obj, basestring):
            obj = str(obj)
        return encode_basestring_ascii(obj)
    if obj is None:
        return 'null'
    elif obj is True or obj is False:
        return obj and 'true' or 'false'
    elif isinstance(obj, (int, long, float)):
        return str(obj)
    elif isinstance(obj, dict):
        return '{%s}' % ','.join('%s:%s' % (
            dumps(key, True),
            dumps(value)
        ) for key, value in obj.iteritems())
    elif isinstance(obj, (tuple, list, set)):
        return '[%s]' % ','.join(dumps(x) for x in obj)
    elif isinstance(obj, basestring):
        return encode_basestring_ascii(obj)
    raise TypeError(type(obj))


def dump(obj, f):
    f.write(dumps(obj))
