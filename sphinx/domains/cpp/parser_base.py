from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any

    from sphinx.config import Config


class BaseParser:
    """Base parser class for C++ domain parsing."""

    def __init__(self, definition: str, location: tuple[str, int] | None = None, config: Config | None = None):
        self.definition = definition
        self.location = location
        self.config = config
        self.pos = 0
        self.end = len(definition)
        self.eof = False
        self._previous_char = None

    @property
    def current_char(self) -> str:
        """Get the current character."""
        if self.pos >= self.end:
            self.eof = True
            return ''
        return self.definition[self.pos]

    def skip_ws(self) -> None:
        """Skip whitespace characters."""
        while not self.eof and self.current_char.isspace():
            self.pos += 1

    def match(self, pattern: str | re.Pattern[str]) -> bool:
        """Try to match a pattern at the current position."""
        if isinstance(pattern, str):
            if self.definition.startswith(pattern, self.pos):
                self.matched_text = pattern
                self.pos += len(pattern)
                return True
        else:
            match = pattern.match(self.definition, self.pos)
            if match:
                self.matched_text = match.group(0)
                self.pos += len(self.matched_text)
                return True
        return False

    def fail(self, message: str) -> None:
        """Report a parsing failure."""
        from sphinx.util.cfamily import DefinitionError
        raise DefinitionError(self.location, message, self.definition, self.pos)

    def expect(self, pattern: str | re.Pattern[str]) -> None:
        """Expect a pattern to match, fail if it doesn't."""
        if not self.match(pattern):
            self.fail(f"Expected pattern {pattern} at position {self.pos}")

    def parse_nested_name(self) -> str:
        """Parse a nested name (e.g., 'std::vector')."""
        # ... implementation would be here
        return ''

    def parse_type(self) -> str:
        """Parse a type specification."""
        # ... implementation would be here
        return ''


# Define __all__ for this module
__all__ = ['BaseParser']
