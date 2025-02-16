class Base:
    #: docstring
    inheritedattr = None

    def inheritedmeth(self):
        """Inherited function."""

    @classmethod
    def inheritedclassmeth(cls):
        """Inherited class method."""

    @staticmethod
    def inheritedstaticmeth(cls):  # NoQA: PLW0211
        """Inherited static method."""


class AnotherBase:
    #: docstring
    def another_inheritedmeth(self):
        """Another inherited function."""


class Derived(Base, AnotherBase):
    def inheritedmeth(self):
        # no docstring here
        pass


class MyList(list):  # NoQA: FURB189
    def meth(self):
        """docstring"""
