# NoQA: N999
# Intentionally no ``from __future__ import annotations``: on Python 3.14+
# these annotations are evaluated lazily (PEP 649), so ``Mapping`` and
# ``Callable`` are only ever looked up by ``annotationlib``.
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Deliberately only available for type checkers; see below.
    from collections.abc import Callable, Mapping  # NoQA: TC004


def convert_to_dict(x: Mapping[str, int]) -> Mapping[str, int]:
    pass


def apply(f: Callable[[str], int], s: str) -> int:
    pass
