"""Test the autodoc extension."""

from __future__ import annotations

import abc
import sys
from importlib import import_module
from typing import Generic, TypeVar

import pytest

from sphinx.ext.autodoc._dynamic._mock import (
    _MockModule,
    _MockObject,
    ismock,
    mock,
    undecorate,
)


def test_MockModule() -> None:
    mock = _MockModule('mocked_module')
    assert isinstance(mock.some_attr, _MockObject)
    assert isinstance(mock.some_method, _MockObject)
    assert isinstance(mock.attr1.attr2, _MockObject)
    assert isinstance(mock.attr1.attr2.meth(), _MockObject)

    assert repr(mock.some_attr) == 'mocked_module.some_attr'
    assert repr(mock.some_method) == 'mocked_module.some_method'
    assert repr(mock.attr1.attr2) == 'mocked_module.attr1.attr2'
    assert repr(mock.attr1.attr2.meth) == 'mocked_module.attr1.attr2.meth'

    assert repr(mock) == 'mocked_module'


def test_MockObject() -> None:
    mock = _MockObject()
    assert isinstance(mock.some_attr, _MockObject)
    assert isinstance(mock.some_method, _MockObject)
    assert isinstance(mock.attr1.attr2, _MockObject)
    assert isinstance(mock.attr1.attr2.meth(), _MockObject)

    # subclassing
    class SubClass(mock.SomeClass):  # type: ignore[misc,name-defined]
        """docstring of SubClass"""

        def method(self):
            return 'string'

    obj = SubClass()
    assert SubClass.__doc__ == 'docstring of SubClass'
    assert isinstance(obj, SubClass)
    assert obj.method() == 'string'
    assert isinstance(obj.other_method(), SubClass)

    # parametrized type
    T = TypeVar('T')

    class SubClass2(mock.SomeClass[T]):  # type: ignore[misc,name-defined]
        """docstring of SubClass"""

    obj2 = SubClass2()  # type: ignore[var-annotated]
    assert SubClass2.__doc__ == 'docstring of SubClass'
    assert isinstance(obj2, SubClass2)


def test_MockObject_generic() -> None:
    mock = _MockObject()

    # parametrized type
    T = TypeVar('T')

    # test subclass with typing.Generic
    # Creating this class would raise an error on Python 3.11+
    # as mock objects are detected as typevars if hasattr(__typing_subst__) is True.

    assert not hasattr(mock.SomeClass, '__typing_subst__')
    S = TypeVar('S')

    class GenericClass(mock.SomeClass, Generic[T, S]):  # type: ignore[misc,name-defined]
        """docstring of GenericSubclass"""

    obj3 = GenericClass()  # type: ignore[var-annotated]
    assert isinstance(obj3, _MockObject)
    assert isinstance(obj3.some_attr, _MockObject)
    assert isinstance(obj3.some_method(), _MockObject)
    assert isinstance(obj3.attr1.attr2, _MockObject)
    assert isinstance(obj3.attr1.attr2.meth(), _MockObject)

    # check that Generic Subscriptions still works

    class GenericSubclass(GenericClass[mock.MockedClass, S]):  # type: ignore[name-defined]
        """docstring of GenericSubclass"""

    assert issubclass(GenericSubclass, GenericClass)


def test_mock() -> None:
    modname = 'sphinx.unknown'
    submodule = modname + '.submodule'
    assert modname not in sys.modules
    with pytest.raises(ImportError):
        import_module(modname)

    with mock([modname]):
        import_module(modname)
        assert modname in sys.modules
        assert isinstance(sys.modules[modname], _MockModule)

        # submodules are also mocked
        import_module(submodule)
        assert submodule in sys.modules
        assert isinstance(sys.modules[submodule], _MockModule)

    assert modname not in sys.modules
    with pytest.raises(ImportError):
        import_module(modname)


def test_mock_does_not_follow_upper_modules() -> None:
    with mock(['sphinx.unknown.module']):  # NoQA: SIM117
        with pytest.raises(ImportError):
            import_module('sphinx.unknown')


def test_abc_MockObject():
    mock = _MockObject()

    class Base:
        @abc.abstractmethod
        def __init__(self):
            pass

    class Derived(Base, mock.SubClass):  # ty: ignore[unsupported-base]
        pass

    obj = Derived()
    assert isinstance(obj, Base)
    assert isinstance(obj, _MockObject)
    assert isinstance(obj.some_method(), Derived)


def test_mock_decorator():
    mock = _MockObject()

    @mock.function_deco
    def func():
        pass

    class Foo:
        @mock.method_deco
        def meth(self):
            pass

        @classmethod
        @mock.method_deco
        def class_meth(cls):
            pass

    @mock.class_deco
    class Bar:
        pass

    @mock.funcion_deco(Foo)
    class Baz:
        pass

    assert undecorate(func).__name__ == 'func'
    assert undecorate(Foo.meth).__name__ == 'meth'
    assert undecorate(Foo.class_meth).__name__ == 'class_meth'
    assert undecorate(Bar).__name__ == 'Bar'
    assert undecorate(Baz).__name__ == 'Baz'


def test_ismock():
    with mock(['sphinx.unknown']):
        mod1 = import_module('sphinx.unknown')
        mod2 = import_module('sphinx.application')

        class Inherited(mod1.Class):
            pass

        assert ismock(mod1) is True
        assert ismock(mod1.Class) is True
        assert ismock(mod1.submod.Class) is True
        assert ismock(Inherited) is False

        assert ismock(mod2) is False
        assert ismock(mod2.Sphinx) is False
