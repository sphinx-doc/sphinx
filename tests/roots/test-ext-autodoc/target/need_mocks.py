import missing_module
import missing_package1.missing_module1
from missing_module import missing_name
from missing_package2 import missing_module2
from missing_package3.missing_module3 import missing_name

import sphinx.missing_module4
from sphinx.missing_module4 import missing_name2


@missing_name(int)
def decoratedFunction():
    """decoratedFunction docstring"""
    return None


def func(arg: missing_module.Class):
    """a function takes mocked object as an argument"""
    pass


class TestAutodoc:
    """TestAutodoc docstring."""

    #: docstring
    Alias = missing_module2.Class

    @missing_name
    def decoratedMethod(self):
        """TestAutodoc::decoratedMethod docstring"""
        return None


class Inherited(missing_module.Class):
    """docstring"""
    pass


sphinx.missing_module4.missing_function(len(missing_name2))

#: docstring
Alias = missing_module2.Class
