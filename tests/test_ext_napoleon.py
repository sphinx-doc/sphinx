# -*- coding: utf-8 -*-
"""
    test_napoleon
    ~~~~~~~~~~~~~

    Tests for :mod:`sphinx.ext.napoleon.__init__` module.


    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from collections import namedtuple
from unittest import TestCase

import mock

from sphinx.application import Sphinx
from sphinx.ext.napoleon import _process_docstring, _skip_member, Config, setup


def _private_doc():
    """module._private_doc.DOCSTRING"""
    pass


def _private_undoc():
    pass


def __special_doc__():
    """module.__special_doc__.DOCSTRING"""
    pass


def __special_undoc__():
    pass


class SampleClass(object):
    def _private_doc(self):
        """SampleClass._private_doc.DOCSTRING"""
        pass

    def _private_undoc(self):
        pass

    def __special_doc__(self):
        """SampleClass.__special_doc__.DOCSTRING"""
        pass

    def __special_undoc__(self):
        pass


class SampleError(Exception):
    def _private_doc(self):
        """SampleError._private_doc.DOCSTRING"""
        pass

    def _private_undoc(self):
        pass

    def __special_doc__(self):
        """SampleError.__special_doc__.DOCSTRING"""
        pass

    def __special_undoc__(self):
        pass


SampleNamedTuple = namedtuple('SampleNamedTuple', 'user_id block_type def_id')


class ProcessDocstringTest(TestCase):
    def test_modify_in_place(self):
        lines = ['Summary line.',
                 '',
                 'Args:',
                 '   arg1: arg1 description']
        app = mock.Mock()
        app.config = Config()
        _process_docstring(app, 'class', 'SampleClass', SampleClass,
                           mock.Mock(), lines)

        expected = ['Summary line.',
                    '',
                    ':param arg1: arg1 description',
                    '']
        self.assertEqual(expected, lines)


class SetupTest(TestCase):
    def test_unknown_app_type(self):
        setup(object())

    def test_add_config_values(self):
        app = mock.Mock(Sphinx)
        setup(app)
        for name, (default, rebuild) in Config._config_values.items():
            has_config = False
            for method_name, args, kwargs in app.method_calls:
                if(method_name == 'add_config_value' and
                   args[0] == name):
                    has_config = True
            if not has_config:
                self.fail('Config value was not added to app %s' % name)

        has_process_docstring = False
        has_skip_member = False
        for method_name, args, kwargs in app.method_calls:
            if method_name == 'connect':
                if(args[0] == 'autodoc-process-docstring' and
                   args[1] == _process_docstring):
                    has_process_docstring = True
                elif(args[0] == 'autodoc-skip-member' and
                     args[1] == _skip_member):
                    has_skip_member = True
        if not has_process_docstring:
            self.fail('autodoc-process-docstring never connected')
        if not has_skip_member:
            self.fail('autodoc-skip-member never connected')


class SkipMemberTest(TestCase):
    def assertSkip(self, what, member, obj, expect_default_skip, config_name):
        skip = True
        app = mock.Mock()
        app.config = Config()
        setattr(app.config, config_name, True)
        if expect_default_skip:
            self.assertEqual(None, _skip_member(app, what, member, obj, skip,
                                                mock.Mock()))
        else:
            self.assertFalse(_skip_member(app, what, member, obj, skip,
                                          mock.Mock()))
        setattr(app.config, config_name, False)
        self.assertEqual(None, _skip_member(app, what, member, obj, skip,
                                            mock.Mock()))

    def test_namedtuple(self):
        self.assertSkip('class', '_asdict',
                        SampleNamedTuple._asdict, False,
                        'napoleon_include_private_with_doc')

    def test_class_private_doc(self):
        self.assertSkip('class', '_private_doc',
                        SampleClass._private_doc, False,
                        'napoleon_include_private_with_doc')

    def test_class_private_undoc(self):
        self.assertSkip('class', '_private_undoc',
                        SampleClass._private_undoc, True,
                        'napoleon_include_private_with_doc')

    def test_class_special_doc(self):
        self.assertSkip('class', '__special_doc__',
                        SampleClass.__special_doc__, False,
                        'napoleon_include_special_with_doc')

    def test_class_special_undoc(self):
        self.assertSkip('class', '__special_undoc__',
                        SampleClass.__special_undoc__, True,
                        'napoleon_include_special_with_doc')

    def test_exception_private_doc(self):
        self.assertSkip('exception', '_private_doc',
                        SampleError._private_doc, False,
                        'napoleon_include_private_with_doc')

    def test_exception_private_undoc(self):
        self.assertSkip('exception', '_private_undoc',
                        SampleError._private_undoc, True,
                        'napoleon_include_private_with_doc')

    def test_exception_special_doc(self):
        self.assertSkip('exception', '__special_doc__',
                        SampleError.__special_doc__, False,
                        'napoleon_include_special_with_doc')

    def test_exception_special_undoc(self):
        self.assertSkip('exception', '__special_undoc__',
                        SampleError.__special_undoc__, True,
                        'napoleon_include_special_with_doc')

    def test_module_private_doc(self):
        self.assertSkip('module', '_private_doc', _private_doc, False,
                        'napoleon_include_private_with_doc')

    def test_module_private_undoc(self):
        self.assertSkip('module', '_private_undoc', _private_undoc, True,
                        'napoleon_include_private_with_doc')

    def test_module_special_doc(self):
        self.assertSkip('module', '__special_doc__', __special_doc__, False,
                        'napoleon_include_special_with_doc')

    def test_module_special_undoc(self):
        self.assertSkip('module', '__special_undoc__', __special_undoc__, True,
                        'napoleon_include_special_with_doc')
