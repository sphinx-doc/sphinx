from __future__ import annotations

__all__ = ()

from io import StringIO
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp, SphinxTestAppWrapperForSkipBuilding


class _CacheEntry(TypedDict):
    """Cached entry in a :class:`ModuleCache`."""

    status: str
    """The application's status output."""
    warning: str
    """The application's warning output."""


class _CacheFrame(TypedDict):
    """The restored cached value."""

    status: StringIO
    """An I/O object initialized to the cached status output."""
    warning: StringIO
    """An I/O object initialized to the cached warning output."""


class ModuleCache:
    __slots__ = ('_cache',)

    def __init__(self) -> None:
        self._cache: dict[str, _CacheEntry] = {}

    def clear(self) -> None:
        """Clear the cache."""
        self._cache.clear()

    def store(self, key: str, app: SphinxTestApp) -> None:
        """Cache some attributes from *app* in the cache.

        :param key: The cache key (usually a ``shared_result``).
        :param app: An application whose attributes are cached.

        The application's attributes being cached are:

        * The content of :attr:`~sphinx.testing.util.SphinxTestApp.status`.
        * The content of :attr:`~sphinx.testing.util.SphinxTestApp.warning`.
        """
        if key not in self._cache:
            status, warning = app.status.getvalue(), app.warning.getvalue()
            self._cache[key] = {'status': status, 'warning': warning}

    def restore(self, key: str) -> _CacheFrame | None:
        """Reconstruct the cached attributes for *key*."""
        if key not in self._cache:
            return None

        data = self._cache[key]
        return {'status': StringIO(data['status']), 'warning': StringIO(data['warning'])}


# XXX: RemovedInSphinx90Warning
class LegacyModuleCache:  # kept for legacy purposes
    cache: dict[str, dict[str, str]] = {}

    def store(
        self, key: str, app_: SphinxTestApp | SphinxTestAppWrapperForSkipBuilding,
    ) -> None:
        if key in self.cache:
            return
        data = {
            'status': app_.status.getvalue(),
            'warning': app_.warning.getvalue(),
        }
        self.cache[key] = data

    def restore(self, key: str) -> dict[str, StringIO]:
        if key not in self.cache:
            return {}

        data = self.cache[key]
        return {
            'status': StringIO(data['status']),
            'warning': StringIO(data['warning']),
        }
