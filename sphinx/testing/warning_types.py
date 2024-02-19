from __future__ import annotations

__all__ = [
    'SphinxTestingWarning',
    'SphinxNodeWarning',
    'SphinxMarkWarning',
    'SphinxFixtureWarning',
]


class SphinxTestingWarning(Warning):
    """Base class for warnings emitted during test configuration."""


class SphinxNodeWarning(SphinxTestingWarning):
    """A warning emitted when an operation on a pytest node failed."""


class SphinxMarkWarning(SphinxNodeWarning):
    """A warning emitted when parsing a marker."""


class SphinxFixtureWarning(SphinxNodeWarning):
    """A warning emitted during a fixture configuration."""
