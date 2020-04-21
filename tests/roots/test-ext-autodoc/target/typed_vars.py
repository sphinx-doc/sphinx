#: attr1
attr1: str = ''
#: attr2
attr2: str
#: attr3
attr3 = ''  # type: str


class Class:
    attr1: int = 0
    attr2: int
    attr3 = 0  # type: int

    def __init__(self):
        self.attr4: int = 0     #: attr4
        self.attr5: int         #: attr5
        self.attr6 = 0          # type: int
        """attr6"""
