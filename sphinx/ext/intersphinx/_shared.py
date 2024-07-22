"""This module contains code shared between intersphinx modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from sphinx.util import logging

if TYPE_CHECKING:
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
    InventoryCacheEntry = tuple[InventoryName, int, Inventory]

    #: The type of :confval:`intersphinx_mapping` *after* normalization.
    IntersphinxMapping = dict[
        InventoryName,
        tuple[InventoryName, tuple[InventoryURI, tuple[InventoryLocation, ...]]],
    ]

LOGGER: Final[logging.SphinxLoggerAdapter] = logging.getLogger('sphinx.ext.intersphinx')


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

    def clear(self) -> None:
        self.env.intersphinx_inventory.clear()  # type: ignore[attr-defined]
        self.env.intersphinx_named_inventory.clear()  # type: ignore[attr-defined]
