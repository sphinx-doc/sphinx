from __future__ import annotations

__all__ = ()

import dataclasses
import itertools
import shutil
from io import StringIO
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from typing import Any

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


@dataclasses.dataclass
class AppInfo:
    """Information to report during the teardown phase of the ``app()`` fixture.

    The information is either rendered as a report section (for ``xdist``
    integration) or directly printed using a ``print`` statement.
    """

    builder: str
    """The builder name."""

    testroot_path: str | None
    """The absolute path to the sources directory (if any)."""
    shared_result: str | None
    """The user-defined shared result (if any)."""

    srcdir: str
    """The absolute path to the application's sources directory."""
    outdir: str
    """The absolute path to the application's output directory."""

    extras: dict[str, Any] = dataclasses.field(default_factory=dict, init=False)
    """Attributes added by :func:`sphinx.testing.fixtures.app_test_info`."""

    # fields below are updated when tearing down :func:`sphinx.testing.fixtures.app`
    _messages: str = dataclasses.field(default='', init=False)
    """The application's status messages (updated by the fixture)."""
    _warnings: str = dataclasses.field(default='', init=False)
    """The application's warnings messages (updated by the fixture)."""

    def update(self, app: SphinxTestApp | SphinxTestAppWrapperForSkipBuilding) -> None:
        """Update the application's status and warning messages."""
        self._messages = app.status.getvalue()
        self._warnings = app.warning.getvalue()

    def render(self, nodeid: str | None = None) -> str:
        """Format the report as a string to print or render.

        :param nodeid: Optional node id to include in the report.
        :return: The formatted information.
        """
        config = [('builder', self.builder)]
        if nodeid:
            config.insert(0, ('test case', nodeid))

        if self.testroot_path:
            config.append(('testroot path', self.testroot_path))
        config.extend([('srcdir', self.srcdir), ('outdir', self.outdir)])
        config.extend((name, repr(value)) for name, value in self.extras.items())

        tw, _ = shutil.get_terminal_size()
        kw = 8 + max(len(name) for name, _ in config)

        lines = itertools.chain(
            [f'{" environment ":-^{tw}}'],
            (f'{name:{kw}s} {strvalue}' for name, strvalue in config),
            [f'{" messages ":-^{tw}}', text] if (text := self._messages) else (),
            [f'{" warnings ":-^{tw}}', text] if (text := self._warnings) else (),
            ['=' * tw],
        )
        return '\n'.join(lines)


# XXX: RemovedInSphinx90Warning
class LegacyModuleCache:  # kept for legacy purposes
    cache: dict[str, dict[str, str]] = {}

    def store(
        self, key: str, app_: SphinxTestApp | SphinxTestAppWrapperForSkipBuilding
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
