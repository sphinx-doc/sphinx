import enum


class EnumCls(enum.Enum):
    """
    this is enum class
    """

    #: doc for val1
    val1 = 12
    val2 = 23  #: doc for val2
    val3 = 34
    """doc for val3"""
    val4 = 34

    def say_hello(self):
        """a method says hello to you."""
        pass

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""
        pass


class EnumClassWithDataType(str, enum.Enum):
    """
    this is enum class
    """

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def say_hello(self):
        """a method says hello to you."""
        pass

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""
        pass


class ToUpperCase:  # not inheriting from enum.Enum
    @property
    def value(self):  # bypass enum.Enum.value
        return str(getattr(self, '_value_')).upper()


class EnumClassWithMixinType(ToUpperCase, enum.Enum):
    """
    this is enum class
    """

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def say_hello(self):
        """a method says hello to you."""
        pass

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""
        pass


class MyMixinEnum(enum.Enum):
    def foo(self):
        return 1


class EnumClassWithMixinEnumType(MyMixinEnum, enum.Enum):
    """
    this is enum class
    """

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def say_hello(self):
        """a method says hello to you."""
        pass

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""
        pass

    def foo(self):
        """new mixin method not found by ``dir``."""
        return 2


class EnumClassWithMixinAndDataType(ToUpperCase, str, enum.Enum):
    """
    this is enum class
    """

    #: doc for val1
    val1 = 'ab'
    val2 = 'cd'  #: doc for val2
    val3 = 'ef'
    """doc for val3"""
    val4 = 'gh'

    def say_hello(self):
        """a method says hello to you."""
        pass

    @classmethod
    def say_goodbye(cls):
        """a classmethod says good-bye to you."""
        pass

    def isupper(self):
        """New isupper method."""
        return False

    def __str__(self):
        """New __str__ method."""
        pass
