from __future__ import annotations

from typing import Generic, TypeVar

_T = TypeVar('_T')


class Holder(Generic[_T]):  # NoQA: UP046
    """A generic class parametrised by a private, undocumented type variable."""
