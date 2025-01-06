"""Inventory utility functions for Sphinx."""

from __future__ import annotations

import posixpath
import re
import zlib
from typing import TYPE_CHECKING

from sphinx.locale import __
from sphinx.util import logging

BUFSIZE = 16 * 1024
logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import os
    from collections.abc import Callable, Sequence
    from typing import Protocol

    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory, InventoryItem

    # Readable file stream for inventory loading
    class _SupportsRead(Protocol):
        def read(self, size: int = ...) -> bytes: ...

    _JoinFunc = Callable[[str, str], str]


def __getattr__(name: str) -> object:
    if name == 'InventoryFileReader':
        from sphinx.util._inventory_file_reader import InventoryFileReader

        return InventoryFileReader
    msg = f'module {__name__!r} has no attribute {name!r}'
    raise AttributeError(msg)


class InventoryFile:
    @classmethod
    def loads(
        cls,
        content: bytes,
        *,
        uri: str,
    ) -> Inventory:
        format_line, _, content = content.partition(b'\n')
        format_line = format_line.rstrip()  # remove trailing \r or spaces
        if format_line == b'# Sphinx inventory version 2':
            return cls._loads_v2(content, uri=uri)
        if format_line == b'# Sphinx inventory version 1':
            lines = content.decode().splitlines()
            return cls._loads_v1(lines, uri=uri)
        if format_line.startswith(b'# Sphinx inventory version '):
            unknown_version = format_line[27:].decode()
            msg = f'unknown or unsupported inventory version: {unknown_version!r}'
            raise ValueError(msg)
        msg = f'invalid inventory header: {format_line.decode()}'
        raise ValueError(msg)

    @classmethod
    def load(cls, stream: _SupportsRead, uri: str, joinfunc: _JoinFunc) -> Inventory:
        return cls.loads(stream.read(), uri=uri)

    @classmethod
    def _loads_v1(cls, lines: Sequence[str], *, uri: str) -> Inventory:
        if len(lines) < 2:
            msg = 'invalid inventory header: missing project name or version'
            raise ValueError(msg)
        invdata: Inventory = {}
        projname = lines[0].rstrip()[11:]  # Project name
        version = lines[1].rstrip()[11:]  # Project version
        for line in lines[2:]:
            name, item_type, location = line.rstrip().split(None, 2)
            location = posixpath.join(uri, location)
            # version 1 did not add anchors to the location
            if item_type == 'mod':
                item_type = 'py:module'
                location += f'#module-{name}'
            else:
                item_type = f'py:{item_type}'
                location += f'#{name}'
            inv_item: InventoryItem = projname, version, location, '-'
            invdata.setdefault(item_type, {})[name] = inv_item
        return invdata

    @classmethod
    def _loads_v2(cls, inv_data: bytes, *, uri: str) -> Inventory:
        try:
            line_1, line_2, check_line, compressed = inv_data.split(b'\n', maxsplit=3)
        except ValueError:
            msg = 'invalid inventory header: missing project name or version'
            raise ValueError(msg) from None
        invdata: Inventory = {}
        projname = line_1.rstrip()[11:].decode()  # Project name
        version = line_2.rstrip()[11:].decode()  # Project version
        # definition -> priority, location, display name
        potential_ambiguities: dict[str, tuple[str, str, str]] = {}
        actual_ambiguities = set()
        if b'zlib' not in check_line:  # '... compressed using zlib'
            msg = f'invalid inventory header (not compressed): {check_line.decode()}'
            raise ValueError(msg)

        decompressed_content = zlib.decompress(compressed)
        for line in decompressed_content.decode().splitlines():
            # be careful to handle names with embedded spaces correctly
            m = re.match(
                r'(.+?)\s+(\S+)\s+(-?\d+)\s+?(\S*)\s+(.*)',
                line.rstrip(),
                flags=re.VERBOSE,
            )
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
            if type in {'std:label', 'std:term'}:
                # Some types require case insensitive matches:
                # * 'term': https://github.com/sphinx-doc/sphinx/issues/9291
                # * 'label': https://github.com/sphinx-doc/sphinx/issues/12008
                definition = f'{type}:{name}'
                content = prio, location, dispname
                lowercase_definition = definition.lower()
                if lowercase_definition in potential_ambiguities:
                    if potential_ambiguities[lowercase_definition] != content:
                        actual_ambiguities.add(definition)
                    else:
                        logger.debug(
                            __('inventory <%s> contains duplicate definitions of %s'),
                            uri,
                            definition,
                            type='intersphinx',
                            subtype='external',
                        )
                else:
                    potential_ambiguities[lowercase_definition] = content
            if location.endswith('$'):
                location = location[:-1] + name
            location = posixpath.join(uri, location)
            inv_item: InventoryItem = projname, version, location, dispname
            invdata.setdefault(type, {})[name] = inv_item
        for ambiguity in actual_ambiguities:
            logger.info(
                __('inventory <%s> contains multiple definitions for %s'),
                uri,
                ambiguity,
                type='intersphinx',
                subtype='external',
            )
        return invdata

    @classmethod
    def dump(
        cls, filename: str | os.PathLike[str], env: BuildEnvironment, builder: Builder
    ) -> None:
        def escape(string: str) -> str:
            return re.sub('\\s+', ' ', string)

        with open(filename, 'wb') as f:
            # header
            f.write(
                (
                    '# Sphinx inventory version 2\n'
                    f'# Project: {escape(env.config.project)}\n'
                    f'# Version: {escape(env.config.version)}\n'
                    '# The remainder of this file is compressed using zlib.\n'
                ).encode()
            )

            # body
            compressor = zlib.compressobj(9)
            for domain in env.domains.sorted():
                sorted_objects = sorted(domain.get_objects())
                for fullname, dispname, type, docname, anchor, prio in sorted_objects:
                    if anchor.endswith(fullname):
                        # this can shorten the inventory by as much as 25%
                        anchor = anchor.removesuffix(fullname) + '$'
                    uri = builder.get_target_uri(docname)
                    if anchor:
                        uri += '#' + anchor
                    if dispname == fullname:
                        dispname = '-'
                    entry = f'{fullname} {domain.name}:{type} {prio} {uri} {dispname}\n'
                    f.write(compressor.compress(entry.encode()))
            f.write(compressor.flush())
