"""Inventory utility functions for Sphinx."""
from __future__ import annotations

import os
import posixpath
import re
import zlib
from typing import IO, TYPE_CHECKING, Callable

from docutils import nodes
from docutils.utils import relative_path

from sphinx.locale import _
from sphinx.util import logging

BUFSIZE = 16 * 1024
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Iterator

    from docutils.nodes import TextElement

    from sphinx.addnodes import pending_xref
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory, InventoryItem


class InventoryFileReader:
    """A file reader for an inventory file.

    This reader supports mixture of texts and compressed texts.
    """

    def __init__(self, stream: IO[bytes]) -> None:
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
    def load(
        cls: type[InventoryFile],
        stream: IO[bytes],
        uri: str,
        joinfunc: Callable[[str, str], str],
    ) -> Inventory:
        reader = InventoryFileReader(stream)
        line = reader.readline().rstrip()
        if line == '# Sphinx inventory version 1':
            return cls.load_v1(reader, uri, joinfunc)
        elif line == '# Sphinx inventory version 2':
            return cls.load_v2(reader, uri, joinfunc)
        else:
            raise ValueError('invalid inventory header: %s' % line)

    @classmethod
    def load_v1(
        cls: type[InventoryFile],
        stream: InventoryFileReader,
        uri: str,
        join: Callable[[str, str], str],
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
        cls: type[InventoryFile],
        stream: InventoryFileReader,
        uri: str,
        join: Callable[[str, str], str],
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
            inv_item: InventoryItem = (projname, version, location, dispname)
            invdata.setdefault(type, {})[name] = inv_item
        return invdata

    @classmethod
    def dump(
        cls: type[InventoryFile], filename: str, env: BuildEnvironment, builder: Builder,
    ) -> None:
        def escape(string: str) -> str:
            return re.sub("\\s+", " ", string)

        with open(os.path.join(filename), 'wb') as f:
            # header
            f.write(('# Sphinx inventory version 2\n'
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
                    entry = ('%s %s:%s %s %s %s\n' %
                             (name, domainname, typ, prio, uri, dispname))
                    f.write(compressor.compress(entry.encode()))
            f.write(compressor.flush())


class InventoryItemSet:
    """Container with intersphinx resolution data.

    Instances of this class is stored by domains and later returned
    during intersphinx reference resolution.
    The implementation details of this class is thus private for intersphinx.

    The data stored is a list of tuples:

    - Element one is a unique reference given in the intersphinx_mapping
      configuration variable.
    - Element two is data about an inventory item in the form of an
      InventoryItem tuple.
    """

    def __init__(self, __items: dict[str | None, list[InventoryItem]] | None = None) -> None:
        if __items is None:
            self._items: dict[str | None, list[InventoryItem]] = {}
        else:
            self._items = __items

    def __repr__(self) -> str:
        return "InventoryItemSet({})".format(self._items)

    def append(self, inventory_name: str | None, item: InventoryItem) -> None:
        self._items.setdefault(inventory_name, []).append(item)

    def select_inventory(self, inv_name: str | None) -> InventoryItemSet:
        """Return inventory items from ``inv_name``.

        If ``inv_name`` is ``None``, return all inventories.
        """
        if inv_name is None:
            return InventoryItemSet(self._items.copy())
        try:
            return InventoryItemSet({inv_name: self._items[inv_name].copy()})
        except KeyError:
            # If inv_name doesn't exist within self._items
            return InventoryItemSet()

    def make_reference_node(
        self,
        domain_name: str,
        node: pending_xref,
        contnode: TextElement,
    ) -> nodes.reference:
        # TODO: document and test
        if len(self._items) == 0:
            msg = "No inventory items!"
            raise ValueError(msg)

        legacy_mapping_items = self._items.get(None, [])
        if len(legacy_mapping_items) == 0:
            inv_name = min(filter(None, self._items))
            proj, version, uri, dispname = self._items[inv_name][0]
        elif len(legacy_mapping_items) == 1:
            # Deprecated path for handling pre-Sphinx 1.0 intersphinx_mapping
            # xref RemovedInSphinx70Warning
            inv_name = "<None>"
            proj, version, uri, dispname = legacy_mapping_items[0]
        else:
            raise AssertionError

        if '://' not in uri and 'refdoc' in node:
            # get correct path in case of subdirectories
            uri = posixpath.join(relative_path(node['refdoc'], '.'), uri)
        if version:
            reftitle = _('(in %s v%s)') % (proj, version)
        else:
            reftitle = _('(in %s)') % proj

        newnode = nodes.reference('', '', internal=False, refuri=uri, reftitle=reftitle)
        if node.get('refexplicit'):
            # use whatever title was given
            newnode.append(contnode)
        elif (dispname == '-'
              or (domain_name == 'std' and node['reftype'] == 'keyword')):
            # use whatever title was given, but strip prefix
            title = contnode.astext()
            if (node.get('origtarget') and node['origtarget'] != node['reftarget']
                    and title.startswith(inv_name + ':')):
                new_title = title[len(inv_name + ':'):]
                newnode.append(contnode.__class__(new_title, new_title))
            else:
                newnode.append(contnode)
        else:
            # else use the given display name (used for :ref:)
            newnode.append(contnode.__class__(dispname, dispname))
        return newnode
