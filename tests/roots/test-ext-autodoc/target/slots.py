class Foo:
    """docstring"""

    __slots__ = ['attr']


class Bar:
    """docstring"""

    __slots__ = {'attr1': 'docstring of attr1',
                 'attr2': 'docstring of attr2',
                 'attr3': None}

    def __init__(self):
        self.attr2 = None  #: docstring of instance attr2


class Baz:
    """docstring"""

    __slots__ = 'attr'
