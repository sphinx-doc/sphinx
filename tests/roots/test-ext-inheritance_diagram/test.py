class Foo:
    pass


class DocHere(Foo):
    pass


class DocLowerLevel(DocHere):
    pass


class DocMainLevel(Foo):
    pass


class Alice(object):
    pass
