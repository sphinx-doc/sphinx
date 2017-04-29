import unicodedata
import six


def _is_source_friendly(ch):  # type: (unicode) -> bool
    """
    Returns true if the given unicode character would be ok in python source
    code.
    """

    # From https://github.com/python/cpython/blob/3.6/Objects/unicodectype.c#L147-L1599
    # not a control or space character
    if not unicodedata.category(ch).startswith(('C', 'Z')):
        return True

    # ascii spaces are fine
    if ch == u' ':
        return True

    # everything else needs escaping
    return False


def _escape(ch): # type: (unicode) -> unicode
    """
    Convert a single unicode character to a representation suitable to place
    inside a single-quoted string.
    """
    # printable characters that have special meanings in literals
    if ch == u'\\':
        return u'\\\\'
    elif ch == u"'":
        return u"\\'"
    elif _is_source_friendly(ch):
        return ch
    else:
        # non-printable characters - convert to \x.., \u...., \U........
        return ch.encode('unicode-escape').decode('ascii')


def urepr(x): # type: (Any) -> unicode
    """
    Return a unicode representation of an object.

    On python 3, repr returns unicode objects, which means that non-ASCII
    characters are rendered in human readable form.
    This provides a similar facility on python 2.
    Additionally, on python 3, it prefixes unicode repr with a u, such that
    the returned repr is a valid unicode literal on both python 2 and python 3.
    """
    if isinstance(x, six.text_type):
        return u"u'{}'".format(
            u''.join(_escape(c) for c in x
        ))
    elif isinstance(x, list):
        return u'[{}]'.format(
            u', '.join(urepr(xi) for xi in x
        ))
    elif isinstance(x, dict):
        return u'{{{}}}'.format(u', '.join(
            u'{}: {}'.format(urepr(k), urepr(v))
            for k, v in x.items()
        ))
    elif six.PY3:
        return repr(x)
    else:
        return repr(x).decode('ascii')
