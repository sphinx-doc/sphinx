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
