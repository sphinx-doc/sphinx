"""
    Two homonymous class

    Could be in 2 different modules
    But it is easier to implement it with nested classes
"""

class A:
    pass

class B:
    class A(A):
        pass

