# -*- coding: utf-8 -*-
"""
    sphinx.util
    ~~~~~~~~~~~

    Utility functions for Sphinx.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
import stat
import time
import errno
import types
import shutil
import fnmatch
import tempfile
import posixpath
import traceback
from os import path

import docutils
import sphinx

# Errnos that we need.
EEXIST = getattr(errno, 'EEXIST', 0)
ENOENT = getattr(errno, 'ENOENT', 0)
EPIPE  = getattr(errno, 'EPIPE', 0)

# Generally useful regular expressions.
ws_re = re.compile(r'\s+')
caption_ref_re = re.compile(r'^([^<]+?)\s*<(.+)>$')
url_re = re.compile(r'(?P<schema>.+)://.*')

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


def docname_join(basedocname, docname):
    return posixpath.normpath(
        posixpath.join('/' + basedocname, '..', docname))[1:]


def ensuredir(path):
    """Ensure that a path exists."""
    try:
        os.makedirs(path)
    except OSError, err:
        # 0 for Jython/Win32
        if err.errno not in [0, EEXIST]:
            raise


def walk(top, topdown=True, followlinks=False):
    """
    Backport of os.walk from 2.6, where the followlinks argument was added.
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


def get_matching_docs(dirname, suffix, exclude_docs=(), exclude_dirs=(),
                      exclude_trees=(), exclude_dirnames=()):
    """
    Get all file names (without suffix) matching a suffix in a
    directory, recursively.

    Exclude docs in *exclude_docs*, exclude dirs in *exclude_dirs*,
    prune dirs in *exclude_trees*, prune dirnames in *exclude_dirnames*.
    """
    pattern = '*' + suffix
    # dirname is a normalized absolute path.
    dirname = path.normpath(path.abspath(dirname))
    dirlen = len(dirname) + 1    # exclude slash
    for root, dirs, files in walk(dirname, followlinks=True):
        if root[dirlen:] in exclude_dirs:
            continue
        if root[dirlen:] in exclude_trees:
            del dirs[:]
            continue
        dirs.sort()
        files.sort()
        for prunedir in exclude_dirnames:
            if prunedir in dirs:
                dirs.remove(prunedir)
        for sfile in files:
            if not fnmatch.fnmatch(sfile, pattern):
                continue
            qualified_name = path.join(root[dirlen:], sfile[:-len(suffix)])
            qualified_name = qualified_name.replace(os.path.sep, SEP)
            if qualified_name in exclude_docs:
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


def save_traceback():
    """
    Save the current exception's traceback in a temporary file.
    """
    exc = traceback.format_exc()
    fd, path = tempfile.mkstemp('.log', 'sphinx-err-')
    os.write(fd, '# Sphinx version: %s\n' % sphinx.__version__)
    os.write(fd, '# Docutils version: %s %s\n' % (docutils.__version__,
                                                  docutils.__version_details__))
    os.write(fd, exc)
    os.close(fd)
    return path


def _translate_pattern(pat):
    """
    Translate a shell-style glob pattern to a regular expression.

    Adapted from the fnmatch module, but enhanced so that single stars don't
    match slashes.
    """
    i, n = 0, len(pat)
    res = ''
    while i < n:
        c = pat[i]
        i += 1
        if c == '*':
            if i < n and pat[i] == '*':
                # double star matches slashes too
                i += 1
                res = res + '.*'
            else:
                # single star doesn't match slashes
                res = res + '[^/]*'
        elif c == '?':
            # question mark doesn't match slashes too
            res = res + '[^/]'
        elif c == '[':
            j = i
            if j < n and pat[j] == '!':
                j += 1
            if j < n and pat[j] == ']':
                j += 1
            while j < n and pat[j] != ']':
                j += 1
            if j >= n:
                res = res + '\\['
            else:
                stuff = pat[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff[0] == '!':
                    # negative pattern mustn't match slashes too
                    stuff = '^/' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\' + stuff
                res = '%s[%s]' % (res, stuff)
        else:
            res += re.escape(c)
    return res + '$'


_pat_cache = {}

def patfilter(names, pat):
    """
    Return the subset of the list NAMES that match PAT.
    Adapted from fnmatch module.
    """
    if pat not in _pat_cache:
        _pat_cache[pat] = re.compile(_translate_pattern(pat))
    match = _pat_cache[pat].match
    return filter(match, names)


no_fn_re = re.compile(r'[^a-zA-Z0-9_-]')

def make_filename(string):
    return no_fn_re.sub('', string)


def nested_parse_with_titles(state, content, node):
    # hack around title style bookkeeping
    surrounding_title_styles = state.memo.title_styles
    surrounding_section_level = state.memo.section_level
    state.memo.title_styles = []
    state.memo.section_level = 0
    try:
        return state.nested_parse(content, 0, node, match_titles=1)
    finally:
        state.memo.title_styles = surrounding_title_styles
        state.memo.section_level = surrounding_section_level


def ustrftime(format, *args):
    # strftime for unicode strings
    return time.strftime(unicode(format).encode('utf-8'), *args).decode('utf-8')


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
            #if not docs:
            #    del self[filename]
            #    self._existing.discard(filename)

    def __getstate__(self):
        return self._existing

    def __setstate__(self, state):
        self._existing = state


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
        except Exception, err:
            raise ValueError('invalid line number spec: %r' % spec)
    return items


def force_decode(string, encoding):
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


def copy_static_entry(source, target, builder, context={}):
    if path.isfile(source):
        if source.lower().endswith('_t'):
            # templated!
            fsrc = open(source, 'rb')
            fdst = open(target[:-2], 'wb')
            fdst.write(builder.templates.render_string(fsrc.read(), context))
            fsrc.close()
            fdst.close()
        else:
            copyfile(source, target)
    elif path.isdir(source):
        if source in builder.config.exclude_dirnames:
            return
        if path.exists(target):
            shutil.rmtree(target)
        shutil.copytree(source, target)


def clean_astext(node):
    """Like node.astext(), but ignore images."""
    node = node.deepcopy()
    for img in node.traverse(docutils.nodes.image):
        img['alt'] = ''
    return node.astext()


# monkey-patch Node.traverse to get more speed
# traverse() is called so many times during a build that it saves
# on average 20-25% overall build time!

def _all_traverse(self):
    """Version of Node.traverse() that doesn't need a condition."""
    result = []
    result.append(self)
    for child in self.children:
        result.extend(child._all_traverse())
    return result

def _fast_traverse(self, cls):
    """Version of Node.traverse() that only supports instance checks."""
    result = []
    if isinstance(self, cls):
        result.append(self)
    for child in self.children:
        result.extend(child._fast_traverse(cls))
    return result

def _new_traverse(self, condition=None,
                 include_self=1, descend=1, siblings=0, ascend=0):
    if include_self and descend and not siblings and not ascend:
        if condition is None:
            return self._all_traverse()
        elif isinstance(condition, (types.ClassType, type)):
            return self._fast_traverse(condition)
    return self._old_traverse(condition, include_self,
                              descend, siblings, ascend)

import docutils.nodes
docutils.nodes.Node._old_traverse = docutils.nodes.Node.traverse
docutils.nodes.Node._all_traverse = _all_traverse
docutils.nodes.Node._fast_traverse = _fast_traverse
docutils.nodes.Node.traverse = _new_traverse
