from typing import TypedDict


class Parent(TypedDict):
    #: parent attr1 doc
    p_attr1: int


class Child(Parent, TypedDict):
    #: child attr1 doc
    c_attr1: int
