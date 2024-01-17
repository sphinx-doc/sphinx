"""Test the autodoc extension.  This tests mainly for private-members option.
"""

import pytest

from tests.test_extensions.test_ext_autodoc import do_autodoc


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_private_field(app):
    app.config.autoclass_content = 'class'
    options = {"members": None}
    actual = do_autodoc(app, 'module', 'target.private', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.private',
        '',
        '',
        '.. py:data:: _PUBLIC_CONSTANT',
        '   :module: target.private',
        '   :value: None',
        '',
        '   :meta public:',
        '',
        '',
        '.. py:function:: _public_function(name)',
        '   :module: target.private',
        '',
        '   public_function is a docstring().',
        '',
        '   :meta public:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_private_field_and_private_members(app):
    app.config.autoclass_content = 'class'
    options = {"members": None,
               "private-members": None}
    actual = do_autodoc(app, 'module', 'target.private', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.private',
        '',
        '',
        '.. py:data:: PRIVATE_CONSTANT',
        '   :module: target.private',
        '   :value: None',
        '',
        '   :meta private:',
        '',
        '',
        '.. py:data:: _PUBLIC_CONSTANT',
        '   :module: target.private',
        '   :value: None',
        '',
        '   :meta public:',
        '',
        '',
        '.. py:function:: _public_function(name)',
        '   :module: target.private',
        '',
        '   public_function is a docstring().',
        '',
        '   :meta public:',
        '',
        '',
        '.. py:function:: private_function(name)',
        '   :module: target.private',
        '',
        '   private_function is a docstring().',
        '',
        '   :meta private:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_private_members(app):
    app.config.autoclass_content = 'class'
    options = {"members": None,
               "private-members": "_PUBLIC_CONSTANT,_public_function"}
    actual = do_autodoc(app, 'module', 'target.private', options)
    assert list(actual) == [
        '',
        '.. py:module:: target.private',
        '',
        '',
        '.. py:data:: _PUBLIC_CONSTANT',
        '   :module: target.private',
        '   :value: None',
        '',
        '   :meta public:',
        '',
        '',
        '.. py:function:: _public_function(name)',
        '   :module: target.private',
        '',
        '   public_function is a docstring().',
        '',
        '   :meta public:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_private_attributes(app):
    app.config.autoclass_content = 'class'
    options = {"members": None}
    actual = do_autodoc(app, 'class', 'target.private.Foo', options)
    assert list(actual) == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.private',
        '',
        '',
        '   .. py:attribute:: Foo._public_attribute',
        '      :module: target.private',
        '      :value: 47',
        '',
        '      A public class attribute whose name starts with an underscore.',
        '',
        '      :meta public:',
        '',
    ]


@pytest.mark.sphinx('html', testroot='ext-autodoc')
def test_private_attributes_and_private_members(app):
    app.config.autoclass_content = 'class'
    options = {"members": None,
               "private-members": None}
    actual = do_autodoc(app, 'class', 'target.private.Foo', options)
    assert list(actual) == [
        '',
        '.. py:class:: Foo()',
        '   :module: target.private',
        '',
        '',
        '   .. py:attribute:: Foo._public_attribute',
        '      :module: target.private',
        '      :value: 47',
        '',
        '      A public class attribute whose name starts with an underscore.',
        '',
        '      :meta public:',
        '',
        '',
        '   .. py:attribute:: Foo.private_attribute',
        '      :module: target.private',
        '      :value: 11',
        '',
        '      A private class attribute whose name does not start with an underscore.',
        '',
        '      :meta private:',
        '',
    ]
