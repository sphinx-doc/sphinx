class Base:
    def inherited_meth(self):
        """Inherited method."""


class Derived(Base):
    @property
    def prop(self):
        """Property with a setter, so its name is defined twice."""
        return 1

    @prop.setter
    def prop(self, value):
        pass

    def first_meth(self):
        """Defined after the property."""

    def last_meth(self):
        """Defined last."""
