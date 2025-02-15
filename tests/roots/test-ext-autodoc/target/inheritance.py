class Base:
    #: docstring
    inheritedattr = None

    def inheritedmeth(self) -> None:
        """Inherited function."""

    @classmethod
    def inheritedclassmeth(cls) -> None:
        """Inherited class method."""

    @staticmethod
    def inheritedstaticmeth(cls) -> None:  # NoQA: PLW0211
        """Inherited static method."""


class AnotherBase:
    #: docstring
    def another_inheritedmeth(self) -> None:
        """Another inherited function."""


class Derived(Base, AnotherBase):
    def inheritedmeth(self) -> None:
        # no docstring here
        pass


class MyList(list):  # NoQA: FURB189
    def meth(self) -> None:
        """docstring"""
