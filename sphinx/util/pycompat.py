# -*- coding: utf-8 -*-
"""
    sphinx.util.pycompat
    ~~~~~~~~~~~~~~~~~~~~

    Stuff for Python version compatibility.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import codecs

# ------------------------------------------------------------------------------
# Python 2/3 compatibility

if sys.version_info >= (3, 0):
    # Python 3
    class_types = (type,)
    # the ubiquitous "bytes" helper functions
    def b(s):
        return s.encode('utf-8')
    bytes = bytes
    # prefix for Unicode strings
    u = ''
    # StringIO/BytesIO classes
    from io import StringIO, BytesIO, TextIOWrapper
    # safely encode a string for printing to the terminal
    def terminal_safe(s):
        return s.encode('ascii', 'backslashreplace').decode('ascii')
    # some kind of default system encoding; should be used with a lenient
    # error handler
    sys_encoding = sys.getdefaultencoding()
    # support for running 2to3 over config files
    def convert_with_2to3(filepath):
        from lib2to3.refactor import RefactoringTool, get_fixers_from_package
        from lib2to3.pgen2.parse import ParseError
        fixers = get_fixers_from_package('lib2to3.fixes')
        refactoring_tool = RefactoringTool(fixers)
        source = refactoring_tool._read_python_source(filepath)[0]
        try:
            tree = refactoring_tool.refactor_string(source, 'conf.py')
        except ParseError, err:
            # do not propagate lib2to3 exceptions
            lineno, offset = err.context[1]
            # try to match ParseError details with SyntaxError details
            raise SyntaxError(err.msg, (filepath, lineno, offset, err.value))
        return unicode(tree)
    from itertools import zip_longest  # Python 3 name

else:
    # Python 2
    from types import ClassType
    class_types = (type, ClassType)
    b = str
    bytes = str
    u = 'u'
    from StringIO import StringIO
    BytesIO = StringIO
    # no need to refactor on 2.x versions
    convert_with_2to3 = None
    def TextIOWrapper(stream, encoding):
        return codecs.lookup(encoding or 'ascii')[2](stream)
    # safely encode a string for printing to the terminal
    def terminal_safe(s):
        return s.encode('ascii', 'backslashreplace')
    # some kind of default system encoding; should be used with a lenient
    # error handler
    import locale
    sys_encoding = locale.getpreferredencoding()
    # use Python 3 name
    from itertools import izip_longest as zip_longest


def execfile_(filepath, _globals):
    from sphinx.util.osutil import fs_encoding
    # get config source -- 'b' is a no-op under 2.x, while 'U' is
    # ignored under 3.x (but 3.x compile() accepts \r\n newlines)
    f = open(filepath, 'rbU')
    try:
        source = f.read()
    finally:
        f.close()

    # py26 accept only LF eol instead of CRLF
    if sys.version_info[:2] == (2, 6):
        source = source.replace(b('\r\n'), b('\n'))

    # compile to a code object, handle syntax errors
    filepath_enc = filepath.encode(fs_encoding)
    try:
        code = compile(source, filepath_enc, 'exec')
    except SyntaxError:
        if convert_with_2to3:
            # maybe the file uses 2.x syntax; try to refactor to
            # 3.x syntax using 2to3
            source = convert_with_2to3(filepath)
            code = compile(source, filepath_enc, 'exec')
        else:
            raise
    exec code in _globals


if sys.version_info >= (3, 2):
    from html import escape as htmlescape  # >= Python 3.2
else:  # 2.6, 2.7, 3.1
    from cgi import escape as htmlescape
