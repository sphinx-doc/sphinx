# -*- coding: utf-8 -*-
"""
    sphinx.util
    ~~~~~~~~~~~

    Utility functions for Sphinx.

    :copyright: 2007 by Georg Brandl.
    :license: Python license.
"""

import os
import sys
import fnmatch
from os import path


# SEP separates path elements in the canonical file names
#
# Define SEP as a manifest constant, not so much because we expect it to change
# in the future as to avoid the suspicion that a stray "/" in the code is a
# hangover from more *nix-oriented origins.
SEP = "/"

def canonical_path(ospath):
    return ospath.replace(os.path.sep, SEP)

def os_path(canpath):
    return canpath.replace(SEP, os.path.sep)


def relative_uri(base, to):
    """Return a relative URL from ``base`` to ``to``."""
    b2 = base.split(SEP)
    t2 = to.split(SEP)
    # remove common segments
    for x, y in zip(b2, t2):
        if x != y:
            break
        b2.pop(0)
        t2.pop(0)
    return ('..' + SEP) * (len(b2)-1) + SEP.join(t2)


def ensuredir(path):
    """Ensure that a path exists."""
    try:
        os.makedirs(path)
    except OSError, err:
        if not err.errno == 17:
            raise


def status_iterator(iterable, colorfunc=lambda x: x, stream=sys.stdout):
    """Print out each item before yielding it."""
    for item in iterable:
        print >>stream, colorfunc(item),
        stream.flush()
        yield item
    print >>stream


def get_matching_files(dirname, pattern, exclude=()):
    """Get all files matching a pattern in a directory, recursively."""
    # dirname is a normalized absolute path.
    dirname = path.normpath(path.abspath(dirname))
    dirlen = len(dirname) + 1    # exclude slash
    for root, dirs, files in os.walk(dirname):
        dirs.sort()
        files.sort()
        for sfile in files:
            if not fnmatch.fnmatch(sfile, pattern):
                continue
            qualified_name = path.join(root[dirlen:], sfile)
            if qualified_name in exclude:
                continue
            yield canonical_path(qualified_name)


def get_category(filename):
    """Get the "category" part of a RST filename."""
    parts = filename.split(SEP, 1)
    if len(parts) < 2:
        return
    return parts[0]


def shorten_result(text='', keywords=[], maxlen=240, fuzz=60):
    if not text:
        text = ''
    text_low = text.lower()
    beg = -1
    for k in keywords:
        i = text_low.find(k.lower())
        if (i > -1 and i < beg) or beg == -1:
            beg = i
    excerpt_beg = 0
    if beg > fuzz:
        for sep in ('.', ':', ';', '='):
            eb = text.find(sep, beg - fuzz, beg - 1)
            if eb > -1:
                eb += 1
                break
        else:
            eb = beg - fuzz
        excerpt_beg = eb
    if excerpt_beg < 0:
        excerpt_beg = 0
    msg = text[excerpt_beg:beg+maxlen]
    if beg > fuzz:
        msg = '... ' + msg
    if beg < len(text)-maxlen:
        msg = msg + ' ...'
    return msg


class attrdict(dict):
    def __getattr__(self, key):
        return self[key]
    def __setattr__(self, key, val):
        self[key] = val
    def __delattr__(self, key):
        del self[key]
