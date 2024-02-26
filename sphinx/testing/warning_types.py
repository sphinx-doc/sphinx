from __future__ import annotations

__all__ = [
    'SphinxTestingWarning',
    'NodeWarning',
    'MarkWarning',
    'FixtureWarning',
]

from _pytest.warning_types import PytestWarning


class SphinxTestingWarning(PytestWarning):
    """Base class for warnings emitted during test configuration."""


class _DeprecationMixin:
    def __init__(self, *args: object, removed_in: tuple[int, ...], **kwargs: object) -> None:
        super().__init__(*args, **kwargs)
        self.removed_in = '.'.join(map(str, removed_in))

    def __str__(self) -> str:
        return f'{super().__str__()} (will be removed in Sphinx {self.removed_in})'


class NodeWarning(SphinxTestingWarning):
    """A warning emitted when an operation on a pytest node failed."""


class MarkWarning(NodeWarning):
    """A warning emitted when parsing a marker."""

    def __init__(self, message: str, mark: str | None = None) -> None:
        message = f'@pytest.mark.{mark}(): {message}' if mark else message
        super().__init__(message)


class MarkDeprecationWarning(_DeprecationMixin, MarkWarning, PendingDeprecationWarning):
    """A deprecation warning emitted in a marker."""


class FixtureWarning(NodeWarning):
    """A warning emitted during a fixture configuration."""

    def __init__(self, message: str, fixturename: str | None = None) -> None:
        message = f'FIXTURE({fixturename!r}): {message}' if fixturename else message
        super().__init__(message)


class FixtureDeprecationWarning(_DeprecationMixin, FixtureWarning, PendingDeprecationWarning):
    """A deprecation warning emitted in a fixture."""
