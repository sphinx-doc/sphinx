# -*- coding: utf-8 -*-
"""
    sphinx.util
    ~~~~~~~~~~~

    Utility functions for Sphinx.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import shutil
import fnmatch
import tempfile
import posixpath
import traceback
from os import path

import docutils
from docutils.utils import relative_path

import jinja2

import sphinx
from sphinx.errors import PycodeError

# import other utilities; partly for backwards compatibility, so don't
# prune unused ones indiscriminately
from sphinx.util.osutil import SEP, os_path, relative_uri, ensuredir, walk, \
     mtimes_of_files, movefile, copyfile, copytimes, make_filename, ustrftime
from sphinx.util.nodes import nested_parse_with_titles, split_explicit_title, \
     explicit_title_re, caption_ref_re
from sphinx.util.matching import patfilter

# Generally useful regular expressions.
ws_re = re.compile(r'\s+')
url_re = re.compile(r'(?P<schema>.+)://.*')


# High-level utility functions.

def docname_join(basedocname, docname):
    return posixpath.normpath(
        posixpath.join('/' + basedocname, '..', docname))[1:]


def get_matching_files(dirname, exclude_matchers=()):
    """
    Get all file names in a directory, recursively.

    Exclude files and dirs matching some matcher in *exclude_matchers*.
    """
    # dirname is a normalized absolute path.
    dirname = path.normpath(path.abspath(dirname))
    dirlen = len(dirname) + 1    # exclude final os.path.sep

    for root, dirs, files in walk(dirname, followlinks=True):
        relativeroot = root[dirlen:]

        qdirs = enumerate(path.join(relativeroot, dn).replace(os.path.sep, SEP)
                          for dn in dirs)
        qfiles = enumerate(path.join(relativeroot, fn).replace(os.path.sep, SEP)
                           for fn in files)
        for matcher in exclude_matchers:
            qdirs = [entry for entry in qdirs if not matcher(entry[1])]
            qfiles = [entry for entry in qfiles if not matcher(entry[1])]

        dirs[:] = sorted(dirs[i] for (i, _) in qdirs)

        for i, filename in sorted(qfiles):
            yield filename


def get_matching_docs(dirname, suffix, exclude_matchers=()):
    """
    Get all file names (without suffix) matching a suffix in a
    directory, recursively.

    Exclude files and dirs matching a pattern in *exclude_patterns*.
    """
    suffixpattern = '*' + suffix
    for filename in get_matching_files(dirname, exclude_matchers):
        if not fnmatch.fnmatch(filename, suffixpattern):
            continue
        yield filename[:-len(suffix)]


class FilenameUniqDict(dict):
    """
    A dictionary that automatically generates unique names for its keys,
    interpreted as filenames, and keeps track of a set of docnames they
    appear in.  Used for images and downloadable files in the environment.
    """
    def __init__(self):
        self._existing = set()

    def add_file(self, docname, newfile):
        if newfile in self:
            self[newfile][0].add(docname)
            return self[newfile][1]
        uniquename = path.basename(newfile)
        base, ext = path.splitext(uniquename)
        i = 0
        while uniquename in self._existing:
            i += 1
            uniquename = '%s%s%s' % (base, i, ext)
        self[newfile] = (set([docname]), uniquename)
        self._existing.add(uniquename)
        return uniquename

    def purge_doc(self, docname):
        for filename, (docs, _) in self.items():
            docs.discard(docname)
            if not docs:
                del self[filename]
                self._existing.discard(filename)

    def __getstate__(self):
        return self._existing

    def __setstate__(self, state):
        self._existing = state


def copy_static_entry(source, targetdir, builder, context={},
                      exclude_matchers=(), level=0):
    """Copy a HTML builder static_path entry from source to targetdir.

    Handles all possible cases of files, directories and subdirectories.
    """
    if exclude_matchers:
        relpath = relative_path(builder.srcdir, source)
        for matcher in exclude_matchers:
            if matcher(relpath):
                return
    if path.isfile(source):
        target = path.join(targetdir, path.basename(source))
        if source.lower().endswith('_t') and builder.templates:
            # templated!
            fsrc = open(source, 'rb')
            fdst = open(target[:-2], 'wb')
            fdst.write(builder.templates.render_string(fsrc.read(), context))
            fsrc.close()
            fdst.close()
        else:
            copyfile(source, target)
    elif path.isdir(source):
        if level == 0:
            for entry in os.listdir(source):
                if entry.startswith('.'):
                    continue
                copy_static_entry(path.join(source, entry), targetdir,
                                  builder, context, level=1,
                                  exclude_matchers=exclude_matchers)
        else:
            target = path.join(targetdir, path.basename(source))
            if path.exists(target):
                shutil.rmtree(target)
            shutil.copytree(source, target)


def save_traceback():
    """
    Save the current exception's traceback in a temporary file.
    """
    import platform
    exc = traceback.format_exc()
    fd, path = tempfile.mkstemp('.log', 'sphinx-err-')
    os.write(fd, '# Sphinx version: %s\n' % sphinx.__version__)
    os.write(fd, '# Python version: %s\n' % platform.python_version())
    os.write(fd, '# Docutils version: %s %s\n' % (docutils.__version__,
                                                  docutils.__version_details__))
    os.write(fd, '# Jinja2 version: %s\n' % jinja2.__version__)
    os.write(fd, exc)
    os.close(fd)
    return path


def get_module_source(modname):
    """Try to find the source code for a module.

    Can return ('file', 'filename') in which case the source is in the given
    file, or ('string', 'source') which which case the source is the string.
    """
    if modname not in sys.modules:
        try:
            __import__(modname)
        except Exception, err:
            raise PycodeError('error importing %r' % modname, err)
    mod = sys.modules[modname]
    if hasattr(mod, '__loader__'):
        try:
            source = mod.__loader__.get_source(modname)
        except Exception, err:
            raise PycodeError('error getting source for %r' % modname, err)
        return 'string', source
    filename = getattr(mod, '__file__', None)
    if filename is None:
        raise PycodeError('no source found for module %r' % modname)
    filename = path.normpath(path.abspath(filename))
    lfilename = filename.lower()
    if lfilename.endswith('.pyo') or lfilename.endswith('.pyc'):
        filename = filename[:-1]
    elif not (lfilename.endswith('.py') or lfilename.endswith('.pyw')):
        raise PycodeError('source is not a .py file: %r' % filename)
    if not path.isfile(filename):
        raise PycodeError('source file is not present: %r' % filename)
    return 'file', filename


# Low-level utility functions and classes.

class Tee(object):
    """
    File-like object writing to two streams.
    """
    def __init__(self, stream1, stream2):
        self.stream1 = stream1
        self.stream2 = stream2

    def write(self, text):
        self.stream1.write(text)
        self.stream2.write(text)


def parselinenos(spec, total):
    """
    Parse a line number spec (such as "1,2,4-6") and return a list of
    wanted line numbers.
    """
    items = list()
    parts = spec.split(',')
    for part in parts:
        try:
            begend = part.strip().split('-')
            if len(begend) > 2:
                raise ValueError
            if len(begend) == 1:
                items.append(int(begend[0])-1)
            else:
                start = (begend[0] == '') and 0 or int(begend[0])-1
                end = (begend[1] == '') and total or int(begend[1])
                items.extend(xrange(start, end))
        except Exception:
            raise ValueError('invalid line number spec: %r' % spec)
    return items


def force_decode(string, encoding):
    """Forcibly get a unicode string out of a bytestring."""
    if isinstance(string, str):
        if encoding:
            string = string.decode(encoding)
        else:
            try:
                # try decoding with utf-8, should only work for real UTF-8
                string = string.decode('utf-8')
            except UnicodeError:
                # last resort -- can't fail
                string = string.decode('latin1')
    return string


class attrdict(dict):
    def __getattr__(self, key):
        return self[key]
    def __setattr__(self, key, val):
        self[key] = val
    def __delattr__(self, key):
        del self[key]


def rpartition(s, t):
    """Similar to str.rpartition from 2.5, but doesn't return the separator."""
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
