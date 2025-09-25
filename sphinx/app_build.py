from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import IO

    from sphinx.builders import Builder
    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment
    from sphinx.util.build_phase import BuildPhase

    from .application import Sphinx


class BuildManager:
    """Manages build operations for Sphinx application."""

    def __init__(self, app: Sphinx) -> None:
        self.app = app

    def build(self, force_all: bool = False, filenames: Sequence[Path] = ()) -> None:
        """Build the documentation."""
        # Implementation would be here
        pass

    def create_builder(self, name: str) -> Builder:
        """Create a builder instance."""
        # Implementation would be here
        pass

    def preload_builder(self, name: str) -> None:
        """Preload a builder."""
        # Implementation would be here
        pass

    def _init_builder(self) -> None:
        """Initialize the builder."""
        # Implementation would be here
        pass


class ProgressTracker:
    """Tracks build progress and status."""

    def __init__(
        self,
        status: IO[str] | None = None,
        warning: IO[str] | None = None,
        verbosity: int = 0,
    ) -> None:
        self.status = status
        self.warning = warning
        self.verbosity = verbosity

    def update(self, message: str, *args: Any) -> None:
        """Update progress message."""
        if self.status and self.verbosity > 0:
            print(message % args, file=self.status)

    def warn(self, message: str, *args: Any) -> None:
        """Emit a warning."""
        if self.warning:
            print(message % args, file=self.warning)


# Define __all__ for this module
__all__ = ['BuildManager', 'ProgressTracker']
