def private_function(name):
    """private_function is a docstring().

    :meta private:
    """

def _public_function(name):
    """public_function is a docstring().

    :meta public:
    """


PRIVATE_CONSTANT = None  #: :meta private:
_PUBLIC_CONSTANT = None  #: :meta public:


class Foo:
    #: A public class attribute whose name starts with an underscore.
    #:
    #: :meta public:
    _public_attribute = 47

    #: A private class attribute whose name does not start with an underscore.
    #:
    #: :meta private:
    private_attribute = 11
