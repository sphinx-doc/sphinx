# -*- coding: utf-8 -*-
"""
    test_ext_autodoc_importer
    ~~~~~~~~~~~~~~~~~~~~~~~~~

    Test the autodoc extension.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.ext.autodoc.importer import _MockObject


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
