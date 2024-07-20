"""This module contains code shared between intersphinx modules."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Union

from sphinx.util import logging

if TYPE_CHECKING:
    from sphinx.environment import BuildEnvironment
    from sphinx.util.typing import Inventory

    InventoryCacheEntry = tuple[Union[str, None], int, Inventory]

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
