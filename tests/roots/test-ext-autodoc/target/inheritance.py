class Base:
    #: docstring
    inheritedattr = None

    def inheritedmeth(self):
        """Inherited function."""

    @classmethod
    def inheritedclassmeth(cls):
        """Inherited class method."""

    @staticmethod
    def inheritedstaticmeth(cls):
        """Inherited static method."""


class AnotherBase:
    #: docstring
    def another_inheritedmeth(self):
        """Another inherited function."""

class Derived(Base, AnotherBase):
    def inheritedmeth(self):
        # no docstring here
        pass


class MyList(list):
    def meth(self):
        """docstring"""
