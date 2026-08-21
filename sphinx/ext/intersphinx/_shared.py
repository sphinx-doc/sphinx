"""This module contains code shared between intersphinx modules."""

from __future__ import annotations

import weakref
from typing import TYPE_CHECKING

from sphinx.util import logging

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any, Final, NoReturn

    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory

    #: The inventory project URL to which links are resolved.
    #:
    #: This value is unique in :confval:`intersphinx_mapping`.
    InventoryURI = str

    #: The inventory (non-empty) name.
    #:
    #: It is unique and in bijection with an inventory remote URL.
    InventoryName = str

    #: A target (local or remote) containing the inventory data to fetch.
    #:
    #: Empty strings are not expected and ``None`` indicates the default
    #: inventory file name :data:`~sphinx.builder.html.INVENTORY_FILENAME`.
    InventoryLocation = str | None

    #: Inventory cache entry. The integer field is the cache expiration time.
    type InventoryCacheEntry = tuple[InventoryName, int, Inventory]

    #: The type of :confval:`intersphinx_mapping` *after* normalisation.
    IntersphinxMapping = dict[
        InventoryName,
        tuple[InventoryName, tuple[InventoryURI, tuple[InventoryLocation, ...]]],
    ]

LOGGER: Final[logging.SphinxLoggerAdapter] = logging.getLogger('sphinx.ext.intersphinx')


class _IntersphinxProject:
    name: InventoryName
    target_uri: InventoryURI
    locations: tuple[InventoryLocation, ...]

    __slots__ = {
        'name':       'The inventory name. '
                      'It is unique and in bijection with an remote inventory URL.',
        'target_uri': 'The inventory project URL to which links are resolved. '
                      'It is unique and in bijection with an inventory name.',
        'locations':  'A tuple of local or remote targets containing '
                      'the inventory data to fetch. '
                      'None indicates the default inventory file name.',
    }  # fmt: skip

    def __init__(
        self,
        *,
        name: InventoryName,
        target_uri: InventoryURI,
        locations: Sequence[InventoryLocation],
    ) -> None:
        if not name or not isinstance(name, str):
            msg = 'name must be a non-empty string'
            raise ValueError(msg)
        if not target_uri or not isinstance(target_uri, str):
            msg = 'target_uri must be a non-empty string'
            raise ValueError(msg)
        if not locations or not isinstance(locations, tuple):
            msg = 'locations must be a non-empty tuple'
            raise ValueError(msg)
        if any(
            location is not None and (not location or not isinstance(location, str))
            for location in locations
        ):
            msg = 'locations must be a tuple of strings or None'
            raise ValueError(msg)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, 'target_uri', target_uri)
        object.__setattr__(self, 'locations', tuple(locations))

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'name={self.name!r}, '
            f'target_uri={self.target_uri!r}, '
            f'locations={self.locations!r})'
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _IntersphinxProject):
            return NotImplemented
        return (
            self.name == other.name
            and self.target_uri == other.target_uri
            and self.locations == other.locations
        )

    def __hash__(self) -> int:
        return hash((self.name, self.target_uri, self.locations))

    def __setattr__(self, key: str, value: Any) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __delattr__(self, key: str) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)


class _CaseInsensitiveIndex:
    """Case-insensitive name index for a single inventory.

    Maps a lower-cased object name to the matching names in insertion order.
    Only ``std:label`` and ``std:term`` are looked up case-insensitively,
    so the per-object-type indices are built lazily, on first use.
    """

    __slots__ = ('_indices', '_inventory', '_sizes')

    def __init__(self, inventory: Inventory) -> None:
        self._inventory = inventory
        self._indices: dict[str, dict[str, list[str]]] = {}
        self._sizes: dict[str, int] = {}

    def matches(self, objtype: str, target_lower: str) -> Sequence[str]:
        """Names of *objtype* whose lower-cased form is *target_lower*."""
        objects = self._inventory[objtype]
        index = self._indices.get(objtype)
        if index is None or self._sizes[objtype] != len(objects):
            # the size check catches inventories mutated after the index was built
            index = {}
            for name in objects:
                index.setdefault(name.lower(), []).append(name)
            self._indices[objtype] = index
            self._sizes[objtype] = len(objects)
        return index.get(target_lower, ())


#: Case-insensitive indices, keyed by build environment.
#: Kept off the environment itself so that they are never pickled.
_CASE_INSENSITIVE_INDICES: weakref.WeakKeyDictionary[
    BuildEnvironment, dict[InventoryName | None, _CaseInsensitiveIndex]
] = weakref.WeakKeyDictionary()


class InventoryAdapter:
    """Inventory adapter for environment"""

    def __init__(self, env: BuildEnvironment) -> None:
        self.env = env

        if not hasattr(env, 'intersphinx_cache'):
            # initial storage when fetching inventories before processing
            self.env.intersphinx_cache = {}  # type: ignore[attr-defined]

            self.env.intersphinx_inventory = {}  # type: ignore[attr-defined]
            self.env.intersphinx_named_inventory = {}  # type: ignore[attr-defined]

    @property
    def cache(self) -> dict[InventoryURI, InventoryCacheEntry]:
        """Intersphinx cache.

        - Key is the URI of the remote inventory.
        - Element one is the key given in the Sphinx :confval:`intersphinx_mapping`.
        - Element two is a time value for cache invalidation, an integer.
        - Element three is the loaded remote inventory of type :class:`!Inventory`.
        """
        return self.env.intersphinx_cache  # type: ignore[attr-defined]

    @property
    def main_inventory(self) -> Inventory:
        return self.env.intersphinx_inventory  # type: ignore[attr-defined]

    @property
    def named_inventory(self) -> dict[InventoryName, Inventory]:
        return self.env.intersphinx_named_inventory  # type: ignore[attr-defined]

    def case_insensitive_index(
        self, inv_name: InventoryName | None
    ) -> _CaseInsensitiveIndex:
        """Case-insensitive index for a named inventory, or the main inventory."""
        indices = _CASE_INSENSITIVE_INDICES.setdefault(self.env, {})
        try:
            return indices[inv_name]
        except KeyError:
            if inv_name is None:
                inventory = self.main_inventory
            else:
                inventory = self.named_inventory[inv_name]
            index = indices[inv_name] = _CaseInsensitiveIndex(inventory)
            return index

    def clear(self) -> None:
        self.env.intersphinx_inventory.clear()  # type: ignore[attr-defined]
        self.env.intersphinx_named_inventory.clear()  # type: ignore[attr-defined]
        _CASE_INSENSITIVE_INDICES.pop(self.env, None)
