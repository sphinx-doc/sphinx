import enum


class EnumCls(enum.Enum):
    """this is enum class"""

    #: doc for val1
    val1 = 12
    val2 = 23  #: doc for val2
    val3 = 34
    """doc for val3"""
    val4 = 34

    def say_hello(self):
        """a method says hello to you."""

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""


class EnumClassWithDataType(str, enum.Enum):
    """this is enum class"""

    x = 'x'

    def say_hello(self):
        """a method says hello to you."""

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""


class ToUpperCase:  # not inheriting from enum.Enum
    @property
    def value(self):  # bypass enum.Enum.value
        return str(getattr(self, '_value_')).upper()


class Greeter:
    def say_hello(self):
        """a method says hello to you."""

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""


class EnumClassWithMixinType(ToUpperCase, enum.Enum):
    """this is enum class"""

    x = 'x'

    def say_hello(self):
        """a method says hello to you."""

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""


class EnumClassWithMixinTypeInherit(Greeter, ToUpperCase, enum.Enum):
    """this is enum class"""

    x = 'x'


class Overridden(enum.Enum):
    def override(self):
        """old override"""
        return 1


class EnumClassWithMixinEnumType(Greeter, Overridden, enum.Enum):
    """this is enum class"""

    x = 'x'

    def override(self):
        """new mixin method not found by ``dir``."""
        return 2


class EnumClassWithMixinAndDataType(Greeter, ToUpperCase, str, enum.Enum):
    """this is enum class"""

    x = 'x'

    def say_hello(self):
        """a method says hello to you."""

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""

    def isupper(self):
        """New isupper method."""
        return False

    def __str__(self):
        """New __str__ method."""
        return super().__str__()


class _EmptyMixinEnum(Greeter, Overridden, enum.Enum):
    """empty mixin class"""


class EnumClassWithParentEnum(_EmptyMixinEnum, ToUpperCase, str, enum.Enum):
    """docstring"""

    x = 'x'

    def isupper(self):
        """New isupper method."""
        return False

    def __str__(self):
        """New __str__ method."""
        return super().__str__()


class EnumClassRedefineMixinConflict(ToUpperCase, enum.Enum):
    """docstring"""


class _MissingRedefineInNonEnumMixin:
    """docstring"""

    @classmethod
    def _missing_(cls, value):
        """base docstring"""
        return super()._missing_(value)


class _MissingRedefineInEnumMixin(enum.Enum):
    """docstring"""

    @classmethod
    def _missing_(cls, value):
        """base docstring"""
        return super()._missing_(value)


class EnumRedefineMissingInNonEnumMixin(_MissingRedefineInNonEnumMixin, enum.Enum):
    """docstring"""


class EnumRedefineMissingInEnumMixin(_MissingRedefineInEnumMixin, enum.Enum):
    """docstring"""


class EnumRedefineMissingInClass(enum.Enum):
    """docstring"""

    @classmethod
    def _missing_(cls, value):
        """docstring"""
        return super()._missing_(value)


class _NameRedefineInNonEnumMixin:
    """docstring"""

    @property
    def name(self):
        """base docstring"""
        return super().name


class _NameRedefineInEnumMixin(enum.Enum):
    """docstring"""

    @property
    def name(self):
        """base docstring"""
        return super().name


class EnumRedefineNameInNonEnumMixin(_NameRedefineInNonEnumMixin, enum.Enum):
    """docstring"""


class EnumRedefineNameInEnumMixin(_NameRedefineInEnumMixin, enum.Enum):
    """docstring"""


class EnumRedefineNameInClass(enum.Enum):
    """docstring"""


    @property
    def name(self):
        """docstring"""
        return super().name
