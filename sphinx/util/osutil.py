# -*- coding: utf-8 -*-
"""
    sphinx.util.osutil
    ~~~~~~~~~~~~~~~~~~

    Operating system-related utility functions for Sphinx.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import time
import errno
import locale
import shutil
import gettext
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
    # remove common segments (except the last segment)
    for x, y in zip(b2[:-1], t2[:-1]):
        if x != y:
            break
        b2.pop(0)
        t2.pop(0)
    if b2 == t2:
        # Special case: relative_uri('f/index.html','f/index.html')
        # returns '', not 'index.html'
        return ''
    if len(b2) == 1 and t2 == ['']:
        # Special case: relative_uri('f/index.html','f/') should
        # return './', not ''
        return '.' +  SEP
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
        try:
            fullpath = path.join(top, name)
        except UnicodeError:
            print >>sys.stderr, (
                '%s:: ERROR: non-ASCII filename not supported on this '
                'filesystem encoding %r, skipped.' % (name, fs_encoding))
            continue
        if path.isdir(fullpath):
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
    return no_fn_re.sub('', string) or 'sphinx'

if sys.version_info < (3, 0):
    # strftime for unicode strings
    def ustrftime(format, *args):
        # if a locale is set, the time strings are encoded in the encoding
        # given by LC_TIME; if that is available, use it
        enc = locale.getlocale(locale.LC_TIME)[1] or 'utf-8'
        return time.strftime(unicode(format).encode(enc), *args).decode(enc)
else:
    ustrftime = time.strftime


def safe_relpath(path, start=None):
    from sphinx.util.pycompat import relpath
    try:
        return relpath(path, start)
    except ValueError:
        return path

def find_catalog(docname, compaction):
    if compaction:
        ret = docname.split(SEP, 1)[0]
    else:
        ret = docname

    return ret


def find_catalog_files(docname, srcdir, locale_dirs, lang, compaction):
    from sphinx.util.pycompat import relpath
    if not(lang and locale_dirs):
        return []

    domain = find_catalog(docname, compaction)
    files = [gettext.find(domain, path.join(srcdir, dir_), [lang])
             for dir_ in locale_dirs]
    files = [relpath(f, srcdir) for f in files if f]
    return files


fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()


if sys.version_info < (3, 0):
    bytes = str
else:
    bytes = bytes


def abspath(pathdir):
    pathdir = path.abspath(pathdir)
    if isinstance(pathdir, bytes):
        pathdir = pathdir.decode(fs_encoding)
    return pathdir
