class bar:
    """docstring of target.canonical.foo::bar."""


class baz:
    """docstring of target.canonical.foo::baz."""


class qux:
    """docstring of target.canonical.foo::qux."""


class Outer:
    """docstring of target.canonical.foo::Outer."""

    class Inner:
        """docstring of target.canonical.foo::Outer.Inner"""

        def inner_method(self):
            """docstring of target.canonical.foo::Outer.Inner.inner_method"""

#: doccomment of target.canonical.foo:my_one
my_one = 1