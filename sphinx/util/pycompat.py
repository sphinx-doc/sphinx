# -*- coding: utf-8 -*-
"""
    sphinx.util.pycompat
    ~~~~~~~~~~~~~~~~~~~~

    Stuff for Python version compatibility.

    :copyright: Copyright 2007-2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import codecs
import encodings
import re

try:
    from types import ClassType
    class_types = (type, ClassType)
except ImportError:
    # Python 3
    class_types = (type,)


# the ubiquitous "bytes" helper function
if sys.version_info >= (3, 0):
    def b(s):
        return s.encode('utf-8')
else:
    b = str


encoding_re = re.compile(b(r'coding[=:]\s*([-\w.]+)'))
unicode_literal_re = re.compile(ur"""
(?:
    "(?:[^"\]]*(?:\\.[^"\\]*)*)"|
    '(?:[^'\]]*(?:\\.[^'\\]*)*)'
)
""", re.VERBOSE)


try:
    from lib2to3.refactor import RefactoringTool, get_fixers_from_package
except ImportError:
    _run_2to3 = None
    def should_run_2to3(filepath):
        return False
else:
    def should_run_2to3(filepath):
        # th default source code encoding for python 2.x
        encoding = 'ascii'
        # only the first match of the encoding cookie counts
        encoding_set = False
        f = open(filepath, 'rb')
        try:
            for i, line in enumerate(f):
                if line.startswith(b('#')):
                    if i == 0 and b('python3') in line:
                        return False
                    if not encoding_set:
                        encoding_match = encoding_re.match(line)
                        if encoding_match:
                            encoding = encoding_match.group(1)
                            encodin_set = True
                elif line.strip():
                    try:
                        line = line.decode(encoding)
                    except UnicodeDecodeError:
                        # I'm not sure this will work but let's try it anyway
                        return True
                    if unicode_literal_re.search(line) is not None:
                        return True
        finally:
            f.close()
        return False

    def run_2to3(filepath):
        sys.path.append('..')
        fixers = get_fixers_from_package('lib2to3.fixes')
        fixers.extend(get_fixers_from_package('custom_fixers'))
        refactoring_tool = RefactoringTool(fixers)
        source = refactoring_tool._read_python_source(filepath)[0]
        ast = refactoring_tool.refactor_string(source, 'conf.py')
        return unicode(ast)


try:
    base_exception = BaseException
except NameError:
    base_exception = Exception


try:
    next = next
except NameError:
    # this is on Python 2, where the method is called "next"
    def next(iterator):
        return iterator.next()


try:
    bytes = bytes
except NameError:
    bytes = str


try:
    any = any
    all = all
except NameError:
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


if sys.version_info < (2, 5):
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
