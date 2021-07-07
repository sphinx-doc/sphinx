"""
Test module for napoleon PEP 526 compatibility with numpy style
"""

module_level_var: int = 99
"""This is an example module level variable"""


class PEP526NumpyClass:
    """
    Sample class with PEP 526 annotations and numpy docstring

    Attributes
    ----------
    attr1:
        Attr1 description

    attr2:
        Attr2 description
    """
    attr1: int
    attr2: str
