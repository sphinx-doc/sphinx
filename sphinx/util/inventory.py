"""Inventory utility functions for Sphinx."""
from __future__ import annotations

import os
import re
import zlib
from typing import IO, TYPE_CHECKING, Callable

from sphinx.util import logging

BUFSIZE = 16 * 1024
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory, InventoryItem


class InventoryFileReader:
    """A file reader for an inventory file.

    This reader supports mixture of texts and compressed texts.
    """

    def __init__(self, stream: IO) -> None:
        self.stream = stream
        self.buffer = b''
        self.eof = False

    def read_buffer(self) -> None:
        chunk = self.stream.read(BUFSIZE)
        if chunk == b'':
            self.eof = True
        self.buffer += chunk

    def readline(self) -> str:
        pos = self.buffer.find(b'\n')
        if pos != -1:
            line = self.buffer[:pos].decode()
            self.buffer = self.buffer[pos + 1:]
        elif self.eof:
            line = self.buffer.decode()
            self.buffer = b''
        else:
            self.read_buffer()
            line = self.readline()

        return line

    def readlines(self) -> Iterator[str]:
        while not self.eof:
            line = self.readline()
            if line:
                yield line

    def read_compressed_chunks(self) -> Iterator[bytes]:
        decompressor = zlib.decompressobj()
        while not self.eof:
            self.read_buffer()
            yield decompressor.decompress(self.buffer)
            self.buffer = b''
        yield decompressor.flush()

    def read_compressed_lines(self) -> Iterator[str]:
        buf = b''
        for chunk in self.read_compressed_chunks():
            buf += chunk
            pos = buf.find(b'\n')
            while pos != -1:
                yield buf[:pos].decode()
                buf = buf[pos + 1:]
                pos = buf.find(b'\n')


class InventoryFile:
    @classmethod
    def load(cls: type[InventoryFile], stream: IO, uri: str, joinfunc: Callable) -> Inventory:
        reader = InventoryFileReader(stream)
        line = reader.readline().rstrip()
        if line == '# Sphinx inventory version 1':
            return cls.load_v1(reader, uri, joinfunc)
        elif line == '# Sphinx inventory version 2':
            return cls.load_v2(reader, uri, joinfunc)
        elif line == '# Sphinx inventory version 3':
            return cls.load_v3(reader, uri, joinfunc)
        else:
            raise ValueError('invalid inventory header: %s' % line)

    @classmethod
    def load_v1(
        cls: type[InventoryFile], stream: InventoryFileReader, uri: str, join: Callable,
    ) -> Inventory:
        invdata: Inventory = {}
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]
        for line in stream.readlines():
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
    def load_v2(
        cls: type[InventoryFile], stream: InventoryFileReader, uri: str, join: Callable,
    ) -> Inventory:
        invdata: Inventory = {}
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]
        line = stream.readline()
        if 'zlib' not in line:
            raise ValueError('invalid inventory header (not compressed): %s' % line)

        for line in stream.read_compressed_lines():
            # be careful to handle names with embedded spaces correctly
            m = re.match(r'(.+?)\s+(\S+)\s+(-?\d+)\s+?(\S*)\s+(.*)',
                         line.rstrip(), flags=re.VERBOSE)
            if not m:
                continue
            name, type, prio, location, dispname = m.groups()
            if ':' not in type:
                # wrong type value. type should be in the form of "{domain}:{objtype}"
                #
                # Note: To avoid the regex DoS, this is implemented in python (refs: #8175)
                continue
            if type == 'py:module' and type in invdata and name in invdata[type]:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue
            if location.endswith('$'):
                location = location[:-1] + name
            location = join(uri, location)
            inv_item: InventoryItem = projname, version, location, dispname
            invdata.setdefault(type, {})[name] = inv_item
        return invdata

    @classmethod
    def load_v3(
        cls: type[InventoryFile], stream: InventoryFileReader, uri: str, join: Callable,
    ) -> Inventory:
        invdata: Inventory = {}
        projname = stream.readline().rstrip()[11:]
        version = stream.readline().rstrip()[11:]
        line = stream.readline()
        if 'zlib' not in line:
            raise ValueError('invalid inventory header (not compressed): %s' % line)

        data_before_name = re.compile(r'^(-?\d+)(:\d+)?\s', flags=re.VERBOSE)
        # pattern when the name does not have spaces
        name_pattern = re.compile(r'^(.+?)\s+\S+\s+?\S*\s+.*', flags=re.VERBOSE)
        # pattern for the string after the name
        data_after_name = re.compile(
            r'^(?P<reftype>\S+)\s+(?P<location>\S*)\s+(?P<dispname>.*)',
            flags=re.VERBOSE,
        )

        for line in stream.read_compressed_lines():
            line = line.rstrip()

            if (before_name := data_before_name.match(line)) is None:
                continue

            s_priority, s_namesize = before_name.groups(None)
            _priority = int(s_priority)  # currently unused

            # remove what was just matched
            line = line[before_name.end():]

            if s_namesize is None:
                if (m := name_pattern.match(line)) is None:
                    continue

                name = m.group(1)
                namesize = len(name)
            else:
                namesize = int(s_namesize[1:])  # remove leading ':'
                name = line[:namesize]
            assert len(name) == namesize

            # remove the 'name' part
            line = line[namesize + 1:]

            if (data := data_after_name.match(line)) is None:
                continue

            reftype, location, dispname = data.groups()

            if ':' not in reftype:
                # wrong type value. type should be in the form of "{domain}:{objtype}"
                #
                # Note: To avoid the regex DoS, this is implemented in python (refs: #8175)
                continue
            if reftype == 'py:module' and reftype in invdata and name in invdata[reftype]:
                # due to a bug in 1.1 and below,
                # two inventory entries are created
                # for Python modules, and the first
                # one is correct
                continue
            if location.endswith('$'):
                location = location[:-1] + name
            location = join(uri, location)
            inv_item: InventoryItem = projname, version, location, dispname
            invdata.setdefault(reftype, {})[name] = inv_item
        return invdata

    @classmethod
    def dump(
        cls: type[InventoryFile], filename: str, env: BuildEnvironment, builder: Builder,
    ) -> None:
        def escape(string: str) -> str:
            return re.sub("\\s+", " ", string)

        with open(os.path.join(filename), 'wb') as f:
            # header
            f.write(('# Sphinx inventory version 3\n'
                     '# Project: %s\n'
                     '# Version: %s\n'
                     '# The remainder of this file is compressed using zlib.\n' %
                     (escape(env.config.project),
                      escape(env.config.version))).encode())

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
                        dispname = '-'

                    # For names with spaces, we need to know exactly where
                    # the ref-type string starts. Technically, we should not
                    # have ':' inside domain or role names, but extensions
                    # may have some weird role names and they could handle
                    # them internally to be docutils compatible. As such,
                    # we encode the length of the name as the priority
                    # fractional part (so that we can easily extract it).
                    slen = f':{len(name)}' if ' ' in name else ''
                    entry = '%s%s %s %s:%s %s %s\n' % (
                        prio, slen, name, domainname, typ, uri, dispname,
                    )
                    f.write(compressor.compress(entry.encode()))
            f.write(compressor.flush())
