class Foo:
    def __init__(self) -> None:
        self.attr1 = None  #: docstring foo
        self.attr2 = None  #: docstring foo


class Bar(Foo):
    def __init__(self) -> None:
        self.attr2 = None  #: docstring bar
        self.attr3 = None  #: docstring bar
        self.attr4 = None
