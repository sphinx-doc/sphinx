# -*- coding: utf-8 -*-
"""
    test_ext_autodoc_importer
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys

import pytest

from sphinx.ext.autodoc.importer import _MockModule, _MockObject, mock


def test_MockObject():
    mock = _MockObject()
    assert isinstance(mock.some_attr, _MockObject)
    assert isinstance(mock.some_method, _MockObject)
    assert isinstance(mock.attr1.attr2, _MockObject)
    assert isinstance(mock.attr1.attr2.meth(), _MockObject)

    class SubClass(mock.SomeClass):
        """docstring of SubClass"""
        def method(self):
            return "string"

    obj = SubClass()
    assert SubClass.__doc__ == "docstring of SubClass"
    assert isinstance(obj, SubClass)
    assert obj.method() == "string"
    assert isinstance(obj.other_method(), SubClass)


def test_mock():
    modname = 'sphinx.unknown'
    submodule = modname + '.submodule'
    assert modname not in sys.modules
    with pytest.raises(ImportError):
        __import__(modname)

    with mock([modname]):
        __import__(modname)
        assert modname in sys.modules
        assert isinstance(sys.modules[modname], _MockModule)

        # submodules are also mocked
        __import__(submodule)
        assert submodule in sys.modules
        assert isinstance(sys.modules[submodule], _MockModule)

    assert modname not in sys.modules
    with pytest.raises(ImportError):
        __import__(modname)


def test_mock_does_not_follow_upper_modules():
    with mock(['sphinx.unknown.module']):
        with pytest.raises(ImportError):
            __import__('sphinx.unknown')
