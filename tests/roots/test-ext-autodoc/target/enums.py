import enum


class EnumClass(enum.Enum):
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

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

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

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def say_hello(self):
        """a method says hello to you."""

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""


class EnumClassWithMixinTypeInherit(Greeter, ToUpperCase, enum.Enum):
    """this is enum class"""

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'


class Overridden(enum.Enum):
    def override(self):
        return 1


class EnumClassWithMixinEnumType(Greeter, Overridden, enum.Enum):
    """this is enum class"""

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def override(self):
        """new mixin method not found by ``dir``."""
        return 2


class EnumClassWithMixinAndDataType(Greeter, ToUpperCase, str, enum.Enum):
    """this is enum class"""

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

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


class _EmptyMixinEnum(Greeter, Overridden, enum.Enum):
    """empty mixin class"""


class ComplexEnumClass(_EmptyMixinEnum, ToUpperCase, str, enum.Enum):
    """this is a complex enum class"""
    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def isupper(self):
        """New isupper method."""
        return False

    def __str__(self):
        """New __str__ method."""


class super_test(str):
    pass