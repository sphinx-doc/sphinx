"""Serialise objects to a stable representation."""

from __future__ import annotations

import hashlib
import types
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def stable_hash(obj: Any) -> str:
    """Return a stable hash for a Python data structure.

    We can't just use the md5 of str(obj) as the order of collections
    may be random.
    """
    if isinstance(obj, dict):
        obj = sorted(map(stable_hash, obj.items()))
    if isinstance(obj, list | tuple | set | frozenset):
        obj = sorted(map(stable_hash, obj))
    elif isinstance(obj, type | types.FunctionType):
        # The default repr() of functions includes the ID, which is not ideal.
        # We use the fully qualified name instead.
        obj = f'{obj.__module__}.{obj.__qualname__}'
    return hashlib.md5(str(obj).encode(), usedforsecurity=False).hexdigest()
