class CustomDataDescriptor(object):
    """Descriptor class docstring."""

    def __init__(self, doc):
        self.__doc__ = doc

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return 42

    def meth(self):
        """Function."""
        return "The Answer"


class CustomDataDescriptorMeta(type):
    """Descriptor metaclass docstring."""


class CustomDataDescriptor2(CustomDataDescriptor):
    """Descriptor class with custom metaclass docstring."""
    __metaclass__ = CustomDataDescriptorMeta


class Class:
    descr = CustomDataDescriptor("Descriptor instance docstring.")

    @property
    def prop(self):
        """Property."""
