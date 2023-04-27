class Foo:
    #: name of Foo
    __name = None
    __age = None


class Bar(Foo):
    __address = None

    #: a member having mangled-like name
    _Baz__email = None
