
import missing_module   # NOQA
import missing_package1.missing_module1   # NOQA
from missing_module import missing_name   # NOQA
from missing_package2 import missing_module2   # NOQA
from missing_package3.missing_module3 import missing_name   # NOQA

import sphinx.missing_module4   # NOQA
from sphinx.missing_module4 import missing_name2   # NOQA


@missing_name
def decoratedFunction():
    """decoratedFunction docstring"""
    return None


class TestAutodoc(object):
    """TestAutodoc docstring."""
    @missing_name
    def decoratedMethod(self):
        """TestAutodoc::decoratedMethod docstring"""
        return None


sphinx.missing_module4.missing_function(len(missing_name2))
