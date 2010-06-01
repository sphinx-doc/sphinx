#!/usr/bin/env python
# coding: utf-8
"""
    path
    ~~~~

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os
import sys
import shutil
from codecs import open


FILESYSTEMENCODING = sys.getfilesystemencoding() or sys.getdefaultencoding()


class path(str):
    if sys.version_info < (3, 0):
        def __new__(cls, s, encoding=FILESYSTEMENCODING, errors=None):
            if isinstance(s, unicode):
                if errors is None:
                    s = s.encode(encoding)
                else:
                    s = s.encode(encoding, errors=errors)
                return str.__new__(cls, s)
            return str.__new__(cls, s)

    @property
    def parent(self):
        return self.__class__(os.path.dirname(self))

    def abspath(self):
        return self.__class__(os.path.abspath(self))

    def isdir(self):
        return os.path.isdir(self)

    def isfile(self):
        return os.path.isfile(self)

    def rmtree(self, ignore_errors=False, onerror=None):
        shutil.rmtree(self, ignore_errors=ignore_errors, onerror=onerror)

    def copytree(self, destination, symlinks=False, ignore=None):
        shutil.copytree(self, destination, symlinks=symlinks, ignore=ignore)

    def unlink(self):
        os.unlink(self)

    def write_text(self, text, **kwargs):
        f = open(self, 'w', **kwargs)
        try:
            f.write(text)
        finally:
            f.close()

    def text(self, **kwargs):
        f = open(self, mode='U', **kwargs)
        try:
            return f.read()
        finally:
            f.close()

    def exists(self):
        return os.path.exists(self)

    def makedirs(self, mode=0777):
        os.makedirs(self, mode)

    def joinpath(self, *args):
        return self.__class__(os.path.join(self, *map(self.__class__, args)))

    __div__ = __truediv__ = joinpath

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, str.__repr__(self))
