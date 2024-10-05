from __future__ import annotations

from gettext import NullTranslations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from io import StringIO


class Foo:
    attr1: StringIO


def spam(ham: Iterable[str]) -> tuple[NullTranslations, bool]:
    pass
