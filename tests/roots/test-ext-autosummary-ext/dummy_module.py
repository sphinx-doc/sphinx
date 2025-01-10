"""
.. autosummary::

   module_attr
   C.class_attr
   C.instance_attr
   C.prop_attr1
   C.prop_attr2
   C.C2
"""


def with_sentence():
    """I have a sentence which
    spans multiple lines. Then I have
    more stuff
    """
    pass


def no_sentence():
    """this doesn't start with a
    capital. so it's not considered
    a sentence
    """
    pass


def empty_line():
    """This is the real summary

    However, it did't end with a period.
    """
    pass


#: This is a module attribute
#:
#: value is integer.
module_attr = 1


class C:
    """
    My C class

    with class_attr attribute
    """

    #: This is a class attribute
    #:
    #: value is integer.
    class_attr = 42

    def __init__(self):
        #: This is an instance attribute
        #:
        #: value is a string
        self.instance_attr = '42'

    def _prop_attr_get(self):
        """
        This is a function docstring

        return value is string.
        """
        return 'spam egg'

    prop_attr1 = property(_prop_attr_get)

    prop_attr2 = property(_prop_attr_get)
    """
    This is a attribute docstring

    value is string.
    """

    class C2:
        """
        This is a nested inner class docstring
        """


def func(arg_, *args, **kwargs):
    """Test function take an argument ended with underscore."""
