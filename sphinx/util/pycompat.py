# -*- coding: utf-8 -*-
"""
    sphinx.util.pycompat
    ~~~~~~~~~~~~~~~~~~~~

    Stuff for Python version compatibility.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import codecs
import encodings

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


try:
    from html import escape as htmlescape
except ImportError:
    from cgi import escape as htmlescape

# ------------------------------------------------------------------------------
# Missing builtins and itertools in Python < 2.6

if sys.version_info >= (2, 6):
    # Python >= 2.6
    next = next

    from itertools import product
    try:
        from itertools import zip_longest  # Python 3 name
    except ImportError:
        from itertools import izip_longest as zip_longest

else:
    # Python < 2.6
    from itertools import izip, repeat, chain

    # this is on Python 2, where the method is called "next" (it is refactored
    # to __next__ by 2to3, but in that case never executed)
    def next(iterator):
        return iterator.next()

    # These replacement functions have been taken from the Python 2.6
    # itertools documentation.
    def product(*args, **kwargs):
        pools = map(tuple, args) * kwargs.get('repeat', 1)
        result = [[]]
        for pool in pools:
            result = [x + [y] for x in result for y in pool]
        for prod in result:
            yield tuple(prod)

    def zip_longest(*args, **kwds):
        # zip_longest('ABCD', 'xy', fillvalue='-') --> Ax By C- D-
        fillvalue = kwds.get('fillvalue')
        def sentinel(counter = ([fillvalue]*(len(args)-1)).pop):
            yield counter()   # yields the fillvalue, or raises IndexError
        fillers = repeat(fillvalue)
        iters = [chain(it, sentinel(), fillers) for it in args]
        try:
            for tup in izip(*iters):
                yield tup
        except IndexError:
            pass


# ------------------------------------------------------------------------------
# Missing builtins and codecs in Python < 2.5

if sys.version_info >= (2, 5):
    # Python >= 2.5
    base_exception = BaseException
    any = any
    all = all

else:
    # Python 2.4
    base_exception = Exception

    def all(gen):
        for i in gen:
            if not i:
                return False
        return True

    def any(gen):
        for i in gen:
            if i:
                return True
        return False

    # Python 2.4 doesn't know the utf-8-sig encoding, so deliver it here

    def my_search_function(encoding):
        norm_encoding = encodings.normalize_encoding(encoding)
        if norm_encoding != 'utf_8_sig':
            return None
        return (encode, decode, StreamReader, StreamWriter)

    codecs.register(my_search_function)

    # begin code copied from utf_8_sig.py in Python 2.6

    def encode(input, errors='strict'):
        return (codecs.BOM_UTF8 +
                codecs.utf_8_encode(input, errors)[0], len(input))

    def decode(input, errors='strict'):
        prefix = 0
        if input[:3] == codecs.BOM_UTF8:
            input = input[3:]
            prefix = 3
        (output, consumed) = codecs.utf_8_decode(input, errors, True)
        return (output, consumed+prefix)

    class StreamWriter(codecs.StreamWriter):
        def reset(self):
            codecs.StreamWriter.reset(self)
            try:
                del self.encode
            except AttributeError:
                pass

        def encode(self, input, errors='strict'):
            self.encode = codecs.utf_8_encode
            return encode(input, errors)

    class StreamReader(codecs.StreamReader):
        def reset(self):
            codecs.StreamReader.reset(self)
            try:
                del self.decode
            except AttributeError:
                pass

        def decode(self, input, errors='strict'):
            if len(input) < 3:
                if codecs.BOM_UTF8.startswith(input):
                    # not enough data to decide if this is a BOM
                    # => try again on the next call
                    return (u"", 0)
            elif input[:3] == codecs.BOM_UTF8:
                self.decode = codecs.utf_8_decode
                (output, consumed) = codecs.utf_8_decode(input[3:],errors)
                return (output, consumed+3)
            # (else) no BOM present
            self.decode = codecs.utf_8_decode
            return codecs.utf_8_decode(input, errors)

    # end code copied from utf_8_sig.py
