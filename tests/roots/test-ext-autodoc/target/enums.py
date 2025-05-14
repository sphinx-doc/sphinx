# ruff: NoQA: PIE796
import enum
from typing import final


class MemberType:
    """Custom data type with a simple API."""

    # this mangled attribute will never be shown on subclasses
    # even if :inherited-members: and :private-members: are set
    __slots__ = ('__data',)

    def __new__(cls, value):
        self = object.__new__(cls)
        self.__data = value
        return self

    def __str__(self):
        """inherited"""
        return self.__data

    def __repr__(self):
        return repr(self.__data)

    def __reduce__(self):
        # data types must be pickable, otherwise enum classes using this data
        # type will be forced to be non-pickable and have their __module__ set
        # to '<unknown>' instead of, for instance, '__main__'
        return self.__class__, (self.__data,)

    @final
    @property
    def dtype(self):
        """docstring"""
        return 'str'

    def isupper(self):
        """inherited"""
        return self.__data.isupper()


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


class EnumClassWithDataType(MemberType, enum.Enum):
    """this is enum class"""

    x = 'x'

    def say_hello(self):
        """docstring"""

    @classmethod
    def say_goodbye(cls):
        """docstring"""


class ToUpperCase:  # not inheriting from enum.Enum
    @property
    def value(self):  # bypass enum.Enum.value
        """uppercased"""
        return str(self._value_).upper()  # type: ignore[attr-defined]


class Greeter:
    def say_hello(self):
        """inherited"""

    @classmethod
    def say_goodbye(cls):
        """inherited"""


class EnumClassWithMixinType(ToUpperCase, enum.Enum):
    """this is enum class"""

    x = 'x'

    def say_hello(self):
        """docstring"""

    @classmethod
    def say_goodbye(cls):
        """docstring"""


class EnumClassWithMixinTypeInherit(Greeter, ToUpperCase, enum.Enum):
    """this is enum class"""

    x = 'x'


class Overridden(enum.Enum):
    def override(self):
        """inherited"""
        return 1


class EnumClassWithMixinEnumType(Greeter, Overridden, enum.Enum):
    """this is enum class"""

    x = 'x'

    def override(self):
        """overridden"""
        return 2


class EnumClassWithMixinAndDataType(Greeter, ToUpperCase, MemberType, enum.Enum):
    """this is enum class"""

    x = 'x'

    def say_hello(self):
        """overridden"""

    @classmethod
    def say_goodbye(cls):
        """overridden"""

    def isupper(self):
        """overridden"""
        return False

    def __str__(self):
        """overridden"""
        return super().__str__()


class _ParentEnum(Greeter, Overridden, enum.Enum):
    """docstring"""


class EnumClassWithParentEnum(ToUpperCase, MemberType, _ParentEnum, enum.Enum):
    """this is enum class"""

    x = 'x'

    def isupper(self):
        """overridden"""
        return False

    def __str__(self):
        """overridden"""
        return super().__str__()


class _SunderMissingInNonEnumMixin:
    @classmethod
    def _missing_(cls, value):
        """inherited"""
        return super()._missing_(value)  # type: ignore[misc]


class _SunderMissingInEnumMixin(enum.Enum):
    @classmethod
    def _missing_(cls, value):
        """inherited"""
        return super()._missing_(value)


class _SunderMissingInDataType(MemberType):
    @classmethod
    def _missing_(cls, value):
        """inherited"""
        return super()._missing_(value)  # type: ignore[misc]


class EnumSunderMissingInNonEnumMixin(_SunderMissingInNonEnumMixin, enum.Enum):
    """this is enum class"""


class EnumSunderMissingInEnumMixin(_SunderMissingInEnumMixin, enum.Enum):
    """this is enum class"""


class EnumSunderMissingInDataType(_SunderMissingInDataType, enum.Enum):
    """this is enum class"""


class EnumSunderMissingInClass(enum.Enum):
    """this is enum class"""

    @classmethod
    def _missing_(cls, value):
        """docstring"""
        return super()._missing_(value)


class _NamePropertyInNonEnumMixin:
    @property
    def name(self):
        """inherited"""
        return super().name  # type: ignore[misc]


class _NamePropertyInEnumMixin(enum.Enum):
    @property
    def name(self):
        """inherited"""
        return super().name


class _NamePropertyInDataType(MemberType):
    @property
    def name(self):
        """inherited"""
        return super().name  # type: ignore[misc]


class EnumNamePropertyInNonEnumMixin(_NamePropertyInNonEnumMixin, enum.Enum):
    """this is enum class"""


class EnumNamePropertyInEnumMixin(_NamePropertyInEnumMixin, enum.Enum):
    """this is enum class"""


class EnumNamePropertyInDataType(_NamePropertyInDataType, enum.Enum):
    """this is enum class"""


class EnumNamePropertyInClass(enum.Enum):
    """this is enum class"""

    @property
    def name(self):
        """docstring"""
        return super().name
