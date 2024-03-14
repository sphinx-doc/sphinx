"""Private utililty functions for :mod:`sphinx.testing.plugin`.

This module is an implementation detail and any provided function
or class can be altered, removed or moved without prior notice.
"""

from __future__ import annotations

__all__ = ()

import binascii
import json
import os
import pickle
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, overload

import pytest

if TYPE_CHECKING:
    from typing import Any

    from _pytest.nodes import Node as PytestNode

    from sphinx.testing.internal.pytest_util import TestNodeLocation


# fmt: off
@overload
def make_unique_id() -> str: ...  # NoQA: E704
@overload
def make_unique_id(prefix: str | os.PathLike[str]) -> str: ...  # NoQA: E704
# fmt: on
def make_unique_id(prefix: str | os.PathLike[str] | None = None) -> str:  # NoQA: E302
    r"""Generate a 128-bit unique identifier prefixed by *prefix*.

    :param prefix: An optional prefix to prepend to the unique identifier.
    :return: A unique identifier.
    """
    suffix = os.urandom(16).hex()  # 128-bits of entropy
    return '-'.join((os.fsdecode(prefix), suffix)) if prefix else suffix


def get_environ_checksum(*args: Any) -> int:
    """Compute a CRC-32 checksum of *args*."""
    def default_encoder(x: object) -> str:
        try:
            return pickle.dumps(x, protocol=pickle.HIGHEST_PROTOCOL).hex()
        except (NotImplementedError, TypeError, ValueError):
            return hex(id(x))[2:]

    # use the most compact JSON format
    env = json.dumps(args, ensure_ascii=False, sort_keys=True, indent=None,
                     separators=(',', ':'), default=default_encoder)
    # avoid using unique_object_id() since we do not really need SHA-1 entropy
    return binascii.crc32(env.encode('utf-8', errors='backslashreplace'))


# Use a LRU cache to speed-up the generation of the UUID-5 value
# when generating the object ID for parametrized sub-tests (those
# sub-tests will be using the same "object id") since UUID-5 is
# based on SHA-1.
@lru_cache(maxsize=65536)
def unique_object_id(name: str) -> str:
    """Get a unique hexadecimal identifier for an object name.

    :param name: The name of the object to get a unique ID of.
    :return: A unique hexadecimal identifier for *name*.
    """
    # ensure that non UTF-8 characters are supported and handled similarly
    sanitized = name.encode('utf-8', errors='backslashreplace').decode('utf-8')
    return uuid.uuid5(uuid.NAMESPACE_OID, sanitized).hex


def get_namespace_id(node: PytestNode) -> str:
    """Get a unique hexadecimal identifier for the node's namespace.

    The node's namespace is defined by all the modules and classes
    the node is part of.
    """
    namespace = '@'.join(filter(None, (
        getattr(t.obj, '__name__', None) or None for t in node.listchain()
        if isinstance(t, (pytest.Module, pytest.Class)) and t.obj
    ))) or node.nodeid
    return unique_object_id(namespace)


def get_location_id(location: TestNodeLocation) -> str:
    """Make a unique ID out of a test node location.

    The ID is based on the physical node location (file and line number)
    and is more precise than :func:`py_location_hash`.
    """
    fspath, lineno = location
    return unique_object_id(f'{fspath}:L{lineno}')
