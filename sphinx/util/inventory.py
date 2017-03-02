# -*- coding: utf-8 -*-
"""
    sphinx.util.inventory
    ~~~~~~~~~~~~~~~~~~~~~

    Inventory utility functions for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import re
import zlib
import codecs

from six import PY3

if False:
    # For type annotation
    from typing import Callable, Dict, IO, Iterator, Tuple  # NOQA

    if PY3:
        unicode = str

    Inventory = Dict[unicode, Dict[unicode, Tuple[unicode, unicode, unicode, unicode]]]


BUFSIZE = 16 * 1024
UTF8StreamReader = codecs.lookup('utf-8')[2]


class ZlibReader(object):
    """Compressed file reader."""

    def __init__(self, stream):
        # type: (IO) -> None
        self.stream = stream

    def read_chunks(self):
        # type: () -> Iterator[bytes]
        decompressor = zlib.decompressobj()
        for chunk in iter(lambda: self.stream.read(BUFSIZE), b''):
            yield decompressor.decompress(chunk)
        yield decompressor.flush()

    def __iter__(self):
        # type: () -> Iterator[unicode]
        buf = b''
        for chunk in self.read_chunks():
            buf += chunk
            pos = buf.find(b'\n')
            while pos != -1:
                yield buf[:pos].decode('utf-8')
                buf = buf[pos + 1:]
                pos = buf.find(b'\n')

        assert not buf

    def readlines(self):
        # type: () -> Iterator[unicode]
        return iter(self)  # type: ignore


class InventoryFile(object):
    @classmethod
    def load(cls, stream, uri, joinfunc):
        # type: (IO, unicode, Callable) -> Inventory
        line = stream.readline().rstrip().decode('utf-8')
        if line == '# Sphinx inventory version 1':
            return cls.load_v1(stream, uri, joinfunc)
        elif line == '# Sphinx inventory version 2':
            return cls.load_v2(stream, uri, joinfunc)
        else:
            raise ValueError('invalid inventory header: %s' % line)

    @classmethod
    def load_v1(cls, stream, uri, join):
        # type: (IO, unicode, Callable) -> Inventory
        stream = UTF8StreamReader(stream)
        invdata = {}  # type: Inventory
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]
        for line in stream:
            name, type, location = line.rstrip().split(None, 2)
            location = join(uri, location)
            # version 1 did not add anchors to the location
            if type == 'mod':
                type = 'py:module'
                location += '#module-' + name
            else:
                type = 'py:' + type
                location += '#' + name
            invdata.setdefault(type, {})[name] = (projname, version, location, '-')
        return invdata

    @classmethod
    def load_v2(cls, stream, uri, join):
        # type: (IO, unicode, Callable) -> Inventory
        invdata = {}  # type: Inventory
        projname = stream.readline().decode('utf-8').rstrip()[11:]
        version = stream.readline().decode('utf-8').rstrip()[11:]
        line = stream.readline().decode('utf-8')
        if 'zlib' not in line:
            raise ValueError('invalid inventory header (not compressed): %s' % line)

        for line in ZlibReader(stream).readlines():
            # be careful to handle names with embedded spaces correctly
            m = re.match(r'(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)',
                         line.rstrip())
            if not m:
                continue
            name, type, prio, location, dispname = m.groups()
            if type == 'py:module' and type in invdata and \
                    name in invdata[type]:  # due to a bug in 1.1 and below,
                                            # two inventory entries are created
                                            # for Python modules, and the first
                                            # one is correct
                continue
            if location.endswith(u'$'):
                location = location[:-1] + name
            location = join(uri, location)
            invdata.setdefault(type, {})[name] = (projname, version,
                                                  location, dispname)
        return invdata
