"""Warnings emitted by the :mod:`sphinx.testing.plugin` plugin."""

from __future__ import annotations

__all__ = ()

from _pytest.warning_types import PytestWarning


class SphinxTestingWarning(PytestWarning):
    """Base class for warnings emitted during test configuration."""


class NodeWarning(SphinxTestingWarning):
    """A warning emitted when an operation on a pytest node failed."""


class MarkWarning(NodeWarning):
    """A warning emitted when parsing a marker."""

    def __init__(self, message: str, markname: str | None = None) -> None:
        message = f'@pytest.mark.{markname}(): {message}' if markname else message
        super().__init__(message)


class FixtureWarning(NodeWarning):
    """A warning emitted during a fixture configuration."""

    def __init__(self, message: str, fixturename: str | None = None) -> None:
        message = f'FIXTURE({fixturename!r}): {message}' if fixturename else message
        super().__init__(message)
