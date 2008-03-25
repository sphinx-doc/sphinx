# -*- coding: utf-8 -*-
"""
    sphinx.util
    ~~~~~~~~~~~

    Utility functions for Sphinx.

    :copyright: 2007-2008 by Georg Brandl.
    :license: BSD.
"""

import os
import sys
import fnmatch
import tempfile
import traceback
from os import path


# SEP separates path elements in the canonical file names
#
# Define SEP as a manifest constant, not so much because we expect it to change
# in the future as to avoid the suspicion that a stray "/" in the code is a
# hangover from more *nix-oriented origins.
SEP = "/"

def os_path(canonicalpath):
    return canonicalpath.replace(SEP, os.path.sep)


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


def get_matching_docs(dirname, suffix, exclude=(), prune=()):
    """
    Get all file names (without suffix) matching a suffix in a
    directory, recursively.

    Exclude files in *exclude*, prune directories in *prune*.
    """
    pattern = '*' + suffix
    # dirname is a normalized absolute path.
    dirname = path.normpath(path.abspath(dirname))
    dirlen = len(dirname) + 1    # exclude slash
    for root, dirs, files in os.walk(dirname):
        dirs.sort()
        files.sort()
        for prunedir in prune:
            if prunedir in dirs:
                dirs.remove(prunedir)
        for sfile in files:
            if not fnmatch.fnmatch(sfile, pattern):
                continue
            qualified_name = path.join(root[dirlen:], sfile[:-len(suffix)])
            qualified_name = qualified_name.replace(os.path.sep, SEP)
            if qualified_name in exclude:
                continue
            yield qualified_name


def mtimes_of_files(dirnames, suffix):
    for dirname in dirnames:
        for root, dirs, files in os.walk(dirname):
            for sfile in files:
                if sfile.endswith(suffix):
                    try:
                        yield path.getmtime(path.join(root, sfile))
                    except EnvironmentError:
                        pass


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


def fmt_ex(ex):
    """Format a single line with an exception description."""
    return traceback.format_exception_only(ex.__class__, ex)[-1].strip()


def rpartition(s, t):
    """Similar to str.rpartition from 2.5."""
    i = s.rfind(t)
    if i != -1:
        return s[:i], s[i+len(t):]
    return '', s


def format_exception_cut_frames(x=1):
    """
    Format an exception with traceback, but only the last x frames.
    """
    typ, val, tb = sys.exc_info()
    #res = ['Traceback (most recent call last):\n']
    res = []
    tbres = traceback.format_tb(tb)
    res += tbres[-x:]
    res += traceback.format_exception_only(typ, val)
    return ''.join(res)


def save_traceback():
    """
    Save the current exception's traceback in a temporary file.
    """
    exc = traceback.format_exc()
    fd, path = tempfile.mkstemp('.log', 'sphinx-err-')
    os.write(fd, exc)
    os.close(fd)
    return path
