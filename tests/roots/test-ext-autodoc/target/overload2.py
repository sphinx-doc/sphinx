from target.overload import Bar
from target.overload import sum


class Baz(Bar):
    pass

__all__ = ['sum', 'Baz']
