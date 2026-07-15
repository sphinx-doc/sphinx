"""Tests for :mod:`sphinx.ext.napoleon.__init__` module."""

from __future__ import annotations

import functools
from collections import namedtuple
from unittest import mock

import pytest

from sphinx.application import Sphinx
from sphinx.ext.napoleon import Config, _process_docstring, _skip_member, setup

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Callable

    from sphinx.ext.autodoc._property_types import _AutodocObjType


def simple_decorator[**P, R](f: Callable[P, R]) -> Callable[P, R]:
    """A simple decorator that does nothing, for tests to use."""

    @functools.wraps(f)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        return f(*args, **kwargs)

    return wrapper


def _private_doc() -> None:
    """module._private_doc.DOCSTRING"""
    pass


def _private_undoc() -> None:
    pass


def __special_doc__() -> None:  # NoQA: N807
    """module.__special_doc__.DOCSTRING"""
    pass


def __special_undoc__() -> None:  # NoQA: N807
    pass


class SampleClass:
    def _private_doc(self) -> None:
        """SampleClass._private_doc.DOCSTRING"""
        pass

    def _private_undoc(self) -> None:
        pass

    def __special_doc__(self) -> None:  # NoQA: PLW3201
        """SampleClass.__special_doc__.DOCSTRING"""
        pass

    def __special_undoc__(self) -> None:  # NoQA: PLW3201
        pass

    @simple_decorator
    def __decorated_func__(self) -> None:  # NoQA: PLW3201
        """Doc"""
        pass


class SampleError(Exception):
    def _private_doc(self) -> None:
        """SampleError._private_doc.DOCSTRING"""
        pass

    def _private_undoc(self) -> None:
        pass

    def __special_doc__(self) -> None:  # NoQA: PLW3201
        """SampleError.__special_doc__.DOCSTRING"""
        pass

    def __special_undoc__(self) -> None:  # NoQA: PLW3201
        pass


SampleNamedTuple = namedtuple('SampleNamedTuple', 'user_id block_type def_id')  # NoQA: PYI024


class TestProcessDocstring:
    def test_modify_in_place(self) -> None:
        lines = [
            'Summary line.',
            '',
            'Args:',
            '   arg1: arg1 description',
        ]
        app = mock.Mock()
        app.config = Config()
        _process_docstring(
            app,
            'class',
            'SampleClass',
            SampleClass,
            mock.Mock(),
            lines,
        )

        expected = [
            'Summary line.',
            '',
            ':param arg1: arg1 description',
            '',
        ]
        assert lines == expected


class TestSetup:
    def test_unknown_app_type(self) -> None:
        setup(object())  # type: ignore[arg-type]

    def test_add_config_values(self) -> None:
        app = mock.Mock(Sphinx)
        setup(app)
        for name, _default, _rebuild, _types in Config._config_values:
            has_config = False
            for method_name, args, _kwargs in app.method_calls:
                if method_name == 'add_config_value' and args[0] == name:
                    has_config = True
            if not has_config:
                pytest.fail('Config value was not added to app %s' % name)

        has_process_docstring = False
        has_skip_member = False
        for method_name, args, _kwargs in app.method_calls:
            if method_name == 'connect':
                if (
                    args[0] == 'autodoc-process-docstring'
                    and args[1] == _process_docstring
                ):
                    has_process_docstring = True
                elif args[0] == 'autodoc-skip-member' and args[1] == _skip_member:
                    has_skip_member = True
        if not has_process_docstring:
            pytest.fail('autodoc-process-docstring never connected')
        if not has_skip_member:
            pytest.fail('autodoc-skip-member never connected')


class TestSkipMember:
    def assert_skip(
        self,
        what: _AutodocObjType,
        member: str,
        obj: object,
        expect_default_skip: bool,
        config_name: str,
    ) -> None:
        skip = True
        app = mock.Mock()
        app.config = Config()
        setattr(app.config, config_name, True)
        if expect_default_skip:
            assert None is _skip_member(app, what, member, obj, skip, mock.Mock())
        else:
            assert _skip_member(app, what, member, obj, skip, mock.Mock()) is False
        setattr(app.config, config_name, False)
        assert None is _skip_member(app, what, member, obj, skip, mock.Mock())

    def test_namedtuple(self) -> None:
        # Since python 3.7, namedtuple._asdict() has not been documented
        # because there is no way to check the method is a member of the
        # namedtuple class.  This testcase confirms only it does not
        # raise an error on building document
        # See: https://github.com/sphinx-doc/sphinx/issues/1455
        self.assert_skip(
            'class',
            '_asdict',
            SampleNamedTuple._asdict,
            True,
            'napoleon_include_private_with_doc',
        )

    def test_class_private_doc(self) -> None:
        self.assert_skip(
            'class',
            '_private_doc',
            SampleClass._private_doc,
            False,
            'napoleon_include_private_with_doc',
        )

    def test_class_private_undoc(self) -> None:
        self.assert_skip(
            'class',
            '_private_undoc',
            SampleClass._private_undoc,
            True,
            'napoleon_include_private_with_doc',
        )

    def test_class_special_doc(self) -> None:
        self.assert_skip(
            'class',
            '__special_doc__',
            SampleClass.__special_doc__,
            False,
            'napoleon_include_special_with_doc',
        )

    def test_class_special_undoc(self) -> None:
        self.assert_skip(
            'class',
            '__special_undoc__',
            SampleClass.__special_undoc__,
            True,
            'napoleon_include_special_with_doc',
        )

    def test_class_decorated_doc(self) -> None:
        self.assert_skip(
            'class',
            '__decorated_func__',
            SampleClass.__decorated_func__,
            False,
            'napoleon_include_special_with_doc',
        )

    def test_exception_private_doc(self) -> None:
        self.assert_skip(
            'exception',
            '_private_doc',
            SampleError._private_doc,
            False,
            'napoleon_include_private_with_doc',
        )

    def test_exception_private_undoc(self) -> None:
        self.assert_skip(
            'exception',
            '_private_undoc',
            SampleError._private_undoc,
            True,
            'napoleon_include_private_with_doc',
        )

    def test_exception_special_doc(self) -> None:
        self.assert_skip(
            'exception',
            '__special_doc__',
            SampleError.__special_doc__,
            False,
            'napoleon_include_special_with_doc',
        )

    def test_exception_special_undoc(self) -> None:
        self.assert_skip(
            'exception',
            '__special_undoc__',
            SampleError.__special_undoc__,
            True,
            'napoleon_include_special_with_doc',
        )

    def test_module_private_doc(self) -> None:
        self.assert_skip(
            'module',
            '_private_doc',
            _private_doc,
            False,
            'napoleon_include_private_with_doc',
        )

    def test_module_private_undoc(self) -> None:
        self.assert_skip(
            'module',
            '_private_undoc',
            _private_undoc,
            True,
            'napoleon_include_private_with_doc',
        )

    def test_module_special_doc(self) -> None:
        self.assert_skip(
            'module',
            '__special_doc__',
            __special_doc__,
            False,
            'napoleon_include_special_with_doc',
        )

    def test_module_special_undoc(self) -> None:
        self.assert_skip(
            'module',
            '__special_undoc__',
            __special_undoc__,
            True,
            'napoleon_include_special_with_doc',
        )
