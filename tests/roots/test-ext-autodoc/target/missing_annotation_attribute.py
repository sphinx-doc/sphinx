from __future__ import annotations

from typing import overload

np = None


class Quantity:
    """A quantity with an optional dependency in its signature."""

    @overload
    def __init__(self, value: np.timedelta64) -> None: ...

    @overload
    def __init__(self, value: int) -> None: ...

    def __init__(self, value: object) -> None:
        pass
