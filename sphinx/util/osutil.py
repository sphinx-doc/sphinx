# -*- coding: utf-8 -*-
"""
    sphinx.util.osutil
    ~~~~~~~~~~~~~~~~~~

    Operating system-related utility functions for Sphinx.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import time
import errno
import shutil
from os import path

# Errnos that we need.
EEXIST = getattr(errno, 'EEXIST', 0)
ENOENT = getattr(errno, 'ENOENT', 0)
EPIPE  = getattr(errno, 'EPIPE', 0)
EINVAL = getattr(errno, 'EINVAL', 0)

# SEP separates path elements in the canonical file names
#
# Define SEP as a manifest constant, not so much because we expect it to change
# in the future as to avoid the suspicion that a stray "/" in the code is a
# hangover from more *nix-oriented origins.
SEP = "/"

def os_path(canonicalpath):
    return canonicalpath.replace(SEP, path.sep)


def relative_uri(base, to):
    """Return a relative URL from ``base`` to ``to``."""
    if to.startswith(SEP):
        return to
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
        # 0 for Jython/Win32
        if err.errno not in [0, EEXIST]:
            raise


def walk(top, topdown=True, followlinks=False):
    """Backport of os.walk from 2.6, where the *followlinks* argument was
    added.
    """
    names = os.listdir(top)

    dirs, nondirs = [], []
    for name in names:
        if path.isdir(path.join(top, name)):
            dirs.append(name)
        else:
            nondirs.append(name)

    if topdown:
        yield top, dirs, nondirs
    for name in dirs:
        fullpath = path.join(top, name)
        if followlinks or not path.islink(fullpath):
            for x in walk(fullpath, topdown, followlinks):
                yield x
    if not topdown:
        yield top, dirs, nondirs


def mtimes_of_files(dirnames, suffix):
    for dirname in dirnames:
        for root, dirs, files in os.walk(dirname):
            for sfile in files:
                if sfile.endswith(suffix):
                    try:
                        yield path.getmtime(path.join(root, sfile))
                    except EnvironmentError:
                        pass


def movefile(source, dest):
    """Move a file, removing the destination if it exists."""
    if os.path.exists(dest):
        try:
            os.unlink(dest)
        except OSError:
            pass
    os.rename(source, dest)


def copytimes(source, dest):
    """Copy a file's modification times."""
    st = os.stat(source)
    if hasattr(os, 'utime'):
        os.utime(dest, (st.st_atime, st.st_mtime))


def copyfile(source, dest):
    """Copy a file and its modification times, if possible."""
    shutil.copyfile(source, dest)
    try:
        # don't do full copystat because the source may be read-only
        copytimes(source, dest)
    except OSError:
        pass


no_fn_re = re.compile(r'[^a-zA-Z0-9_-]')

def make_filename(string):
    return no_fn_re.sub('', string)

if sys.version_info < (3, 0):
    def ustrftime(format, *args):
        # strftime for unicode strings
        return time.strftime(unicode(format).encode('utf-8'), *args) \
                .decode('utf-8')
else:
    ustrftime = time.strftime


def safe_relpath(path, start=None):
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return path

def find_catalog(docname, compaction):
    if compaction:
        ret = docname.split(SEP, 1)[0]
    else:
        ret = docname

    return ret
