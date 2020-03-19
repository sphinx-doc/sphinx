"""
    sphinx.util.osutil
    ~~~~~~~~~~~~~~~~~~

    Operating system-related utility functions for Sphinx.

    :copyright: Copyright 2007-2020 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import contextlib
import errno
import filecmp
import os
import re
import shutil
import sys
import warnings
from io import StringIO
from os import path
from typing import Any, Generator, Iterator, List, Tuple

from sphinx.deprecation import RemovedInSphinx40Warning

try:
    # for ALT Linux (#6712)
    from sphinx.testing.path import path as Path
except ImportError:
    Path = None  # type: ignore

if False:
    # For type annotation
    from typing import Type  # for python3.5.1

# Errnos that we need.
EEXIST = getattr(errno, 'EEXIST', 0)  # RemovedInSphinx40Warning
ENOENT = getattr(errno, 'ENOENT', 0)  # RemovedInSphinx40Warning
EPIPE = getattr(errno, 'EPIPE', 0)    # RemovedInSphinx40Warning
EINVAL = getattr(errno, 'EINVAL', 0)  # RemovedInSphinx40Warning

# SEP separates path elements in the canonical file names
#
# Define SEP as a manifest constant, not so much because we expect it to change
# in the future as to avoid the suspicion that a stray "/" in the code is a
# hangover from more *nix-oriented origins.
SEP = "/"


def os_path(canonicalpath: str) -> str:
    return canonicalpath.replace(SEP, path.sep)


def canon_path(nativepath: str) -> str:
    """Return path in OS-independent form"""
    return nativepath.replace(path.sep, SEP)


def relative_uri(base: str, to: str) -> str:
    """Return a relative URL from ``base`` to ``to``."""
    if to.startswith(SEP):
        return to
    b2 = base.split('#')[0].split(SEP)
    t2 = to.split('#')[0].split(SEP)
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
        return '.' + SEP
    return ('..' + SEP) * (len(b2) - 1) + SEP.join(t2)


def ensuredir(path: str) -> None:
    """Ensure that a path exists."""
    os.makedirs(path, exist_ok=True)


def walk(top: str, topdown: bool = True, followlinks: bool = False) -> Iterator[Tuple[str, List[str], List[str]]]:  # NOQA
    warnings.warn('sphinx.util.osutil.walk() is deprecated for removal. '
                  'Please use os.walk() instead.',
                  RemovedInSphinx40Warning)
    return os.walk(top, topdown=topdown, followlinks=followlinks)


def mtimes_of_files(dirnames: List[str], suffix: str) -> Iterator[float]:
    for dirname in dirnames:
        for root, dirs, files in os.walk(dirname):
            for sfile in files:
                if sfile.endswith(suffix):
                    try:
                        yield path.getmtime(path.join(root, sfile))
                    except OSError:
                        pass


def movefile(source: str, dest: str) -> None:
    """Move a file, removing the destination if it exists."""
    if os.path.exists(dest):
        try:
            os.unlink(dest)
        except OSError:
            pass
    os.rename(source, dest)


def copytimes(source: str, dest: str) -> None:
    """Copy a file's modification times."""
    st = os.stat(source)
    if hasattr(os, 'utime'):
        os.utime(dest, (st.st_atime, st.st_mtime))


def copyfile(source: str, dest: str) -> None:
    """Copy a file and its modification times, if possible.

    Note: ``copyfile`` skips copying if the file has not been changed"""
    if not path.exists(dest) or not filecmp.cmp(source, dest):
        shutil.copyfile(source, dest)
        try:
            # don't do full copystat because the source may be read-only
            copytimes(source, dest)
        except OSError:
            pass


no_fn_re = re.compile(r'[^a-zA-Z0-9_-]')
project_suffix_re = re.compile(' Documentation$')


def make_filename(string: str) -> str:
    return no_fn_re.sub('', string) or 'sphinx'


def make_filename_from_project(project: str) -> str:
    return make_filename(project_suffix_re.sub('', project)).lower()


def relpath(path: str, start: str = os.curdir) -> str:
    """Return a relative filepath to *path* either from the current directory or
    from an optional *start* directory.

    This is an alternative of ``os.path.relpath()``.  This returns original path
    if *path* and *start* are on different drives (for Windows platform).
    """
    try:
        return os.path.relpath(path, start)
    except ValueError:
        return path


safe_relpath = relpath  # for compatibility
fs_encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()


def abspath(pathdir: str) -> str:
    if Path is not None and isinstance(pathdir, Path):
        return pathdir.abspath()
    else:
        pathdir = path.abspath(pathdir)
        if isinstance(pathdir, bytes):
            try:
                pathdir = pathdir.decode(fs_encoding)
            except UnicodeDecodeError:
                raise UnicodeDecodeError('multibyte filename not supported on '
                                         'this filesystem encoding '
                                         '(%r)' % fs_encoding)
        return pathdir


def getcwd() -> str:
    warnings.warn('sphinx.util.osutil.getcwd() is deprecated. '
                  'Please use os.getcwd() instead.',
                  RemovedInSphinx40Warning)
    return os.getcwd()


@contextlib.contextmanager
def cd(target_dir: str) -> Generator[None, None, None]:
    cwd = os.getcwd()
    try:
        os.chdir(target_dir)
        yield
    finally:
        os.chdir(cwd)


class FileAvoidWrite:
    """File-like object that buffers output and only writes if content changed.

    Use this class like when writing to a file to avoid touching the original
    file if the content hasn't changed. This is useful in scenarios where file
    mtime is used to invalidate caches or trigger new behavior.

    When writing to this file handle, all writes are buffered until the object
    is closed.

    Objects can be used as context managers.
    """
    def __init__(self, path: str) -> None:
        self._path = path
        self._io = None  # type: StringIO

    def write(self, data: str) -> None:
        if not self._io:
            self._io = StringIO()
        self._io.write(data)

    def close(self) -> None:
        """Stop accepting writes and write file, if needed."""
        if not self._io:
            raise Exception('FileAvoidWrite does not support empty files.')

        buf = self.getvalue()
        self._io.close()

        try:
            with open(self._path) as old_f:
                old_content = old_f.read()
                if old_content == buf:
                    return
        except OSError:
            pass

        with open(self._path, 'w') as f:
            f.write(buf)

    def __enter__(self) -> "FileAvoidWrite":
        return self

    def __exit__(self, exc_type: "Type[Exception]", exc_value: Exception, traceback: Any) -> bool:  # NOQA
        self.close()
        return True

    def __getattr__(self, name: str) -> Any:
        # Proxy to _io instance.
        if not self._io:
            raise Exception('Must write to FileAvoidWrite before other '
                            'methods can be used')

        return getattr(self._io, name)


def rmtree(path: str) -> None:
    if os.path.isdir(path):
        shutil.rmtree(path)
    else:
        os.remove(path)
