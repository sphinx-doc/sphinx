from typing import Generic, TypeVar

T = TypeVar('T')


# Test that typing.Generic's __new__ method does not mask our class'
# __init__ signature.
class A(Generic[T]):
    """docstring for A"""
    def __init__(self, a, b=None):
        pass
