class Foo:
    pass


class DocHere(Foo):
    pass


class DocSubDir1(DocHere):
    pass


class DocSubDir2(DocSubDir1):
    pass


class DocMainLevel(Foo):
    pass


class Alice(object):  # NoQA: UP004
    pass
