# -*- coding: utf-8 -*-
"""
    sphinx.util.inventory
    ~~~~~~~~~~~~~~~~~~~~~

    Inventory utility functions for Sphinx.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import re
import os
import zlib
import codecs

from six import PY3

from sphinx.util import logging

if False:
    # For type annotation
    from typing import Callable, Dict, IO, Iterator, Tuple  # NOQA

    if PY3:
        unicode = str

    Inventory = Dict[unicode, Dict[unicode, Tuple[unicode, unicode, unicode, unicode]]]


BUFSIZE = 16 * 1024
UTF8StreamReader = codecs.lookup('utf-8')[2]

logger = logging.getLogger(__name__)


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

    @classmethod
    def dump(cls, filename, env, builder):
        # type: (unicode, BuildEnvironment, Builder) -> None
        def escape(string):
            # type: (unicode) -> unicode
            return re.sub("\s+", " ", string).encode('utf-8')

        with open(os.path.join(filename), 'wb') as f:
            # header
            f.write('# Sphinx inventory version 2\n')
            f.write('# Project: %s\n' % escape(env.config.project))
            f.write('# Version: %s\n' % escape(env.config.version))
            f.write('# The remainder of this file is compressed using zlib.\n')

            # body
            compressor = zlib.compressobj(9)
            for domainname, domain in sorted(env.domains.items()):
                for name, dispname, typ, docname, anchor, prio in \
                        sorted(domain.get_objects()):
                    if anchor.endswith(name):
                        # this can shorten the inventory by as much as 25%
                        anchor = anchor[:-len(name)] + '$'
                    uri = builder.get_target_uri(docname)
                    if anchor:
                        uri += '#' + anchor
                    if dispname == name:
                        dispname = u'-'
                    entry = (u'%s %s:%s %s %s %s\n' %
                             (name, domainname, typ, prio, uri, dispname))
                    f.write(compressor.compress(entry.encode('utf-8')))
            f.write(compressor.flush())
