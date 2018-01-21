
import missing_module
from missing_module import missing_name
import missing_package1.missing_module1
from missing_package2 import missing_module2
from missing_package3.missing_module3 import missing_name
import sphinx.missing_module4
from sphinx.missing_module4 import missing_name2

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
