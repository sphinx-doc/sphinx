class A:
    """A class having no __init__, no __new__"""


class B:
    """A class having __init__(no docstring), no __new__"""
    def __init__(self):
        pass


class C:
    """A class having __init__, no __new__"""
    def __init__(self):
        """__init__ docstring"""


class D:
    """A class having no __init__, __new__(no docstring)"""
    def __new__(cls):
        pass


class E:
    """A class having no __init__, __new__"""
    def __new__(cls):
        """__new__ docstring"""


class F:
    """A class having both __init__ and __new__"""
    def __init__(self):
        """__init__ docstring"""

    def __new__(cls):
        """__new__ docstring"""
