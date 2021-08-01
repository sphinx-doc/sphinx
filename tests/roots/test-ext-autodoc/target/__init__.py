import enum
from io import StringIO

from sphinx.util import save_traceback  # NOQA

__all__ = ['Class']

#: documentation for the integer
integer = 1


def raises(exc, func, *args, **kwds):
    """Raise AssertionError if ``func(*args, **kwds)`` does not raise *exc*."""
    pass


class CustomEx(Exception):
    """My custom exception."""

    def f(self):
        """Exception method."""


def _funky_classmethod(name, b, c, d, docstring=None):
    """Generates a classmethod for a class from a template by filling out
    some arguments."""
    def template(cls, a, b, c, d=4, e=5, f=6):
        return a, b, c, d, e, f
    from functools import partial
    function = partial(template, b=b, c=c, d=d)
    function.__name__ = name
    function.__doc__ = docstring
    return classmethod(function)


class Class(object):
    """Class to document."""

    def meth(self):
        """Function."""

    def undocmeth(self):
        pass

    def skipmeth(self):
        """Method that should be skipped."""

    def excludemeth(self):
        """Method that should be excluded."""

    # should not be documented
    skipattr = 'foo'

    #: should be documented -- süß
    attr = 'bar'

    docattr = 'baz'
    """should likewise be documented -- süß"""

    udocattr = 'quux'
    """should be documented as well - süß"""

    # initialized to any class imported from another module
    mdocattr = StringIO()
    """should be documented as well - süß"""

    roger = _funky_classmethod("roger", 2, 3, 4)

    moore = _funky_classmethod("moore", 9, 8, 7,
                               docstring="moore(a, e, f) -> happiness")

    def __init__(self, arg):
        self.inst_attr_inline = None  #: an inline documented instance attr
        #: a documented instance attribute
        self.inst_attr_comment = None
        self.inst_attr_string = None
        """a documented instance attribute"""
        self._private_inst_attr = None  #: a private instance attribute

    def __special1__(self):
        """documented special method"""

    def __special2__(self):
        # undocumented special method
        pass


class CustomDict(dict):
    """Docstring."""


def function(foo, *args, **kwds):
    """
    Return spam.
    """
    pass


class Outer(object):
    """Foo"""

    class Inner(object):
        """Foo"""

        def meth(self):
            """Foo"""

    # should be documented as an alias
    factory = dict


class InnerChild(Outer.Inner):
    """InnerChild docstring"""


class DocstringSig(object):
    def __new__(cls, *new_args, **new_kwargs):
        """__new__(cls, d, e=1) -> DocstringSig
First line of docstring

        rest of docstring
        """

    def __init__(self, *init_args, **init_kwargs):
        """__init__(self, a, b=1) -> None
First line of docstring

        rest of docstring
        """

    def meth(self):
        """meth(FOO, BAR=1) -> BAZ
First line of docstring

        rest of docstring
        """

    def meth2(self):
        """First line, no signature
        Second line followed by indentation::

            indented line
        """

    @property
    def prop1(self):
        """DocstringSig.prop1(self)
        First line of docstring
        """
        return 123

    @property
    def prop2(self):
        """First line of docstring
        Second line of docstring
        """
        return 456


class StrRepr(str):
    """docstring"""

    def __repr__(self):
        return self


class AttCls(object):
    a1 = StrRepr('hello\nworld')
    a2 = None


class InstAttCls(object):
    """Class with documented class and instance attributes."""

    #: Doc comment for class attribute InstAttCls.ca1.
    #: It can have multiple lines.
    ca1 = 'a'

    ca2 = 'b'    #: Doc comment for InstAttCls.ca2. One line only.

    ca3 = 'c'
    """Docstring for class attribute InstAttCls.ca3."""

    def __init__(self):
        #: Doc comment for instance attribute InstAttCls.ia1
        self.ia1 = 'd'

        self.ia2 = 'e'
        """Docstring for instance attribute InstAttCls.ia2."""


class CustomIter(object):
    def __init__(self):
        """Create a new `CustomIter`."""
        self.values = range(10)

    def __iter__(self):
        """Iterate squares of each value."""
        for i in self.values:
            yield i ** 2

    def snafucate(self):
        """Makes this snafucated."""
        print("snafucated")
