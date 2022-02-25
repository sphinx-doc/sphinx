from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import StringIO


class Foo:
    attr1: "StringIO"
