"""Test the intersphinx extension."""

from __future__ import annotations

import posixpath
import re
import shutil
import zlib
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from typing import TYPE_CHECKING

from sphinx.ext.intersphinx._shared import InventoryAdapter
from sphinx.testing.util import SphinxTestApp
from sphinx.util.inventory import _InventoryItem

from tests.utils import http_server

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path
    from typing import Any, BinaryIO

BASE_CONFIG = {
    'extensions': ['sphinx.ext.intersphinx'],
    'intersphinx_timeout': 0.1,
}


class InventoryEntry:
    """Entry in the Intersphinx inventory."""

    __slots__ = (
        'name',
        'display_name',
        'domain_name',
        'object_type',
        'uri',
        'anchor',
        'priority',
    )

    def __init__(
        self,
        name: str = 'this',
        *,
        display_name: str | None = None,
        domain_name: str = 'py',
        object_type: str = 'obj',
        uri: str = 'index.html',
        anchor: str = '',
        priority: int = 0,
    ):
        if anchor.endswith(name):
            anchor = anchor.removesuffix(name) + '$'

        if anchor:
            uri += '#' + anchor

        if display_name is None or display_name == name:
            display_name = '-'

        self.name = name
        self.display_name = display_name
        self.domain_name = domain_name
        self.object_type = object_type
        self.uri = uri
        self.anchor = anchor
        self.priority = priority

    def format(self) -> str:
        """Format the entry as it appears in the inventory file."""
        return (
            f'{self.name} {self.domain_name}:{self.object_type} '
            f'{self.priority} {self.uri} {self.display_name}\n'
        )


class IntersphinxProject:
    def __init__(
        self,
        *,
        name: str = 'spam',
        version: str | int = 1,
        baseurl: str = '',
        baseuri: str = '',
        file: str | None = None,
    ) -> None:
        #: The project name.
        self.name = name
        #: The escaped project name.
        self.safe_name = re.sub(r'\\s+', ' ', name)

        #: The project version as a string.
        self.version = version = str(version)
        #: The escaped project version.
        self.safe_version = re.sub(r'\\s+', ' ', version)

        #: The project base URL (e.g., http://localhost:9341).
        self.baseurl = baseurl
        #: The project base URI, relative to *baseurl* (e.g., 'spam').
        self.uri = baseuri
        #: The project URL, as specified in :confval:`intersphinx_mapping`.
        self.url = posixpath.join(baseurl, baseuri)
        #: The project local file, if any.
        self.file = file

    @property
    def record(self) -> dict[str, tuple[str | None, str | None]]:
        """The :confval:`intersphinx_mapping` record for this project."""
        return {self.name: (self.url, self.file)}

    def normalise(self, entry: InventoryEntry) -> tuple[str, _InventoryItem]:
        """Format an inventory entry as if it were part of this project."""
        return entry.name, _InventoryItem(
            project_name=self.safe_name,
            project_version=self.safe_version,
            uri=posixpath.join(self.url, entry.uri),
            display_name=entry.display_name,
        )


class FakeInventory:
    protocol_version: int

    def __init__(self, project: IntersphinxProject | None = None) -> None:
        self.project = project or IntersphinxProject()

    def serialise(self, entries: Iterable[InventoryEntry] | None = None) -> bytes:
        buffer = BytesIO()
        self._write_headers(buffer)
        entries = entries or [InventoryEntry()]
        self._write_body(buffer, (item.format().encode() for item in entries))
        return buffer.getvalue()

    def _write_headers(self, buffer: BinaryIO) -> None:
        headers = (
            f'# Sphinx inventory version {self.protocol_version}\n'
            f'# Project: {self.project.safe_name}\n'
            f'# Version: {self.project.safe_version}\n'
        ).encode()
        buffer.write(headers)

    def _write_body(self, buffer: BinaryIO, lines: Iterable[bytes]) -> None:
        raise NotImplementedError


class FakeInventoryV2(FakeInventory):
    protocol_version = 2

    def _write_headers(self, buffer: BinaryIO) -> None:
        super()._write_headers(buffer)
        buffer.write(b'# The remainder of this file is compressed using zlib.\n')

    def _write_body(self, buffer: BinaryIO, lines: Iterable[bytes]) -> None:
        compressor = zlib.compressobj(9)
        buffer.writelines(map(compressor.compress, lines))
        buffer.write(compressor.flush())


class SingleEntryProject(IntersphinxProject):
    name = 'spam'
    port = 9341  # needed since otherwise it's an automatic port

    def __init__(
        self,
        version: int,
        route: str,
        *,
        item_name: str = 'ham',
        domain_name: str = 'py',
        object_type: str = 'module',
    ) -> None:
        super().__init__(
            name=self.name,
            version=version,
            baseurl=f'http://localhost:{self.port}',
            baseuri=route,
        )
        self.item_name = item_name
        self.domain_name = domain_name
        self.object_type = object_type
        self.reftype = f'{domain_name}:{object_type}'

    def make_entry(self) -> InventoryEntry:
        """Get an inventory entry for this project."""
        name = f'{self.item_name}_{self.version}'
        return InventoryEntry(
            name, domain_name=self.domain_name, object_type=self.object_type
        )


def make_inventory_handler(
    *projects: SingleEntryProject,
) -> type[BaseHTTPRequestHandler]:
    name, port = projects[0].name, projects[0].port
    assert all(p.name == name for p in projects)
    assert all(p.port == port for p in projects)

    class InventoryHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200, 'OK')

            data = b''
            for project in projects:
                # create the data to return depending on the endpoint
                if self.path.startswith(f'/{project.uri}/'):
                    entry = project.make_entry()
                    data = FakeInventoryV2(project).serialise([entry])
                    break

            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(*args: Any, **kwargs: Any) -> None:
            pass

    return InventoryHandler


def test_intersphinx_project_fixture() -> None:
    # check that our fixture class is correct
    project = SingleEntryProject(1, 'route')
    assert project.url == 'http://localhost:9341/route'


def test_load_mappings_cache(tmp_path: Path) -> None:
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').touch()
    project = SingleEntryProject(1, 'a')

    InventoryHandler = make_inventory_handler(project)
    with http_server(InventoryHandler, port=project.port):
        # clean build
        confoverrides = BASE_CONFIG | {'intersphinx_mapping': project.record}
        app = SphinxTestApp('dummy', srcdir=tmp_path, confoverrides=confoverrides)
        app.build()
        app.cleanup()

    # the inventory when querying the 'old' URL
    entry = project.make_entry()
    item = dict((project.normalise(entry),))
    inventories = InventoryAdapter(app.env)
    assert list(inventories.cache) == ['http://localhost:9341/a']
    e_name, _e_time, e_inv = inventories.cache['http://localhost:9341/a']
    assert e_name == 'spam'
    assert e_inv == {'py:module': item}
    assert inventories.named_inventory == {'spam': {'py:module': item}}


def test_load_mappings_cache_update(tmp_path: Path) -> None:
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').touch()
    old_project = SingleEntryProject(1337, 'old')
    new_project = SingleEntryProject(1701, 'new')

    InventoryHandler = make_inventory_handler(old_project, new_project)
    with http_server(InventoryHandler, port=SingleEntryProject.port):
        # build normally to create an initial cache
        confoverrides1 = BASE_CONFIG | {'intersphinx_mapping': old_project.record}
        app1 = SphinxTestApp('dummy', srcdir=tmp_path, confoverrides=confoverrides1)
        app1.build()
        app1.cleanup()
        shutil.rmtree(app1.doctreedir / '__intersphinx_cache__', ignore_errors=True)

        # switch to new url and assert that the old URL is no more stored
        confoverrides2 = BASE_CONFIG | {'intersphinx_mapping': new_project.record}
        app2 = SphinxTestApp('dummy', srcdir=tmp_path, confoverrides=confoverrides2)
        app2.build()
        app2.cleanup()
        shutil.rmtree(app2.doctreedir / '__intersphinx_cache__', ignore_errors=True)

    entry = new_project.make_entry()
    item = dict((new_project.normalise(entry),))
    inventories = InventoryAdapter(app2.env)
    # check that the URLs were changed accordingly
    assert list(inventories.cache) == ['http://localhost:9341/new']
    e_name, _e_time, e_inv = inventories.cache['http://localhost:9341/new']
    assert e_name == 'spam'
    assert e_inv == {'py:module': item}
    assert inventories.named_inventory == {'spam': {'py:module': item}}


def test_load_mappings_cache_revert_update(tmp_path: Path) -> None:
    tmp_path.joinpath('conf.py').touch()
    tmp_path.joinpath('index.rst').touch()
    old_project = SingleEntryProject(1337, 'old')
    new_project = SingleEntryProject(1701, 'new')

    InventoryHandler = make_inventory_handler(old_project, new_project)
    with http_server(InventoryHandler, port=SingleEntryProject.port):
        # build normally to create an initial cache
        confoverrides1 = BASE_CONFIG | {'intersphinx_mapping': old_project.record}
        app1 = SphinxTestApp('dummy', srcdir=tmp_path, confoverrides=confoverrides1)
        app1.build()
        app1.cleanup()

        # switch to new url and build
        confoverrides2 = BASE_CONFIG | {'intersphinx_mapping': new_project.record}
        app2 = SphinxTestApp('dummy', srcdir=tmp_path, confoverrides=confoverrides2)
        app2.build()
        app2.cleanup()

        # switch back to old url (reuse 'old_item')
        confoverrides3 = BASE_CONFIG | {'intersphinx_mapping': old_project.record}
        app3 = SphinxTestApp('dummy', srcdir=tmp_path, confoverrides=confoverrides3)
        app3.build()
        app3.cleanup()

    entry = old_project.make_entry()
    item = dict((old_project.normalise(entry),))
    inventories = InventoryAdapter(app3.env)
    # check that the URLs were changed accordingly
    assert list(inventories.cache) == ['http://localhost:9341/old']
    e_name, _e_time, e_inv = inventories.cache['http://localhost:9341/old']
    assert e_name == 'spam'
    assert e_inv == {'py:module': item}
    assert inventories.named_inventory == {'spam': {'py:module': item}}
