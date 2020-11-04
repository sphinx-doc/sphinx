from inspect import Parameter, Signature


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
