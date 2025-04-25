from typing import NewType


class Foo:
    """This is class Foo."""


type Pep695Alias = Foo
"""This is PEP695 type alias."""

type Pep695AliasC = dict[
    str, Foo
]  #: This is PEP695 complex type alias with doc comment.

type Pep695AliasUnion = str | int
"""This is PEP695 type alias for union."""

type Pep695AliasOfAlias = Pep695AliasC
"""This is PEP695 type alias of PEP695 alias."""

Bar = NewType('Bar', Pep695Alias)
"""This is newtype of Pep695Alias."""


def ret_pep695(a: Pep695Alias) -> Pep695Alias:
    """This fn accepts and returns PEP695 alias."""
    ...
