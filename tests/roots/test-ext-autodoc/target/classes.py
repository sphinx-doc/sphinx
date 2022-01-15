from inspect import Parameter, Signature
from typing import List, Union


class Foo:
    pass


class Bar:
    def __init__(self, x, y):
        pass


class Baz:
    def __new__(cls, x, y):
        pass


class Qux:
    __signature__ = Signature(parameters=[Parameter('foo', Parameter.POSITIONAL_OR_KEYWORD),
                                          Parameter('bar', Parameter.POSITIONAL_OR_KEYWORD)])

    def __init__(self, x, y):
        pass


class Quux(List[Union[int, float]]):
    """A subclass of List[Union[int, float]]"""
    pass


class Corge(Quux):
    pass


Alias = Foo

#: docstring
OtherAlias = Bar

#: docstring
IntAlias = int
