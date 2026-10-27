import sys

TYPE_CHECKING = False
if sys.version_info[:2] < (3, 14) or TYPE_CHECKING:
    TypeCheckingOnlyName = int


class Foo:
    """docstring"""

    @property
    def prop1(self) -> int:
        """docstring"""

    @classmethod
    @property
    def prop2(cls) -> int:
        """docstring"""

    @property
    def prop1_with_type_comment(self):
        # type: () -> int
        """docstring"""

    @classmethod
    @property
    def prop2_with_type_comment(cls):
        # type: () -> int
        """docstring"""

    @property
    def prop3_with_undefined_anotation(self) -> TypeCheckingOnlyName:
        """docstring"""
