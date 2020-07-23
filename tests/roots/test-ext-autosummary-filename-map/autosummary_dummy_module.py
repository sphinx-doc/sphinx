from os import path  # NOQA
from typing import Union


class Foo:
    class Bar:
        pass

    def __init__(self):
        pass

    def bar(self):
        pass

    @property
    def baz(self):
        pass


def bar(x: Union[int, str], y: int = 1) -> None:
    pass
