from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

from sphinx.testing.matcher.options import CompleteOptions, Options, OptionsHolder

if TYPE_CHECKING:
    from typing import ClassVar

    from sphinx.testing.matcher.options import OptionName


def test_options_class():
    assert len(Options.__annotations__) > 0, 'missing annotations'

    # ensure that the classes are kept synchronized
    missing_keys = Options.__annotations__.keys() - CompleteOptions.__annotations__
    assert not missing_keys, f'missing option(s): {", ".join(missing_keys)}'

    foreign_keys = CompleteOptions.__annotations__.keys() - Options.__annotations__
    assert not foreign_keys, f'unknown option(s): {", ".join(foreign_keys)}'


def test_default_options():
    """Check the synchronization of default options and classes in Sphinx."""
    default_options = OptionsHolder.default_options.copy()

    processed = set()

    def check(option: OptionName, default: object) -> None:
        assert option not in processed
        assert option in default_options
        assert default_options[option] == default
        processed.add(option)

    check('keep_ansi', True)

    check('strip', False)
    check('stripline', False)

    check('keep_break', False)
    check('keep_empty', True)
    check('compress', False)
    check('unique', False)

    check('delete', ())
    check('ignore', None)

    check('flavor', 'none')

    # check that there are no leftover options
    assert sorted(processed) == sorted(Options.__annotations__)


def test_options_holder():
    obj = OptionsHolder()
    assert isinstance(obj.options, MappingProxyType)
    assert isinstance(obj.complete_options, MappingProxyType)

    obj = OptionsHolder()
    assert 'keep_break' not in obj.options
    assert 'keep_break' in obj.complete_options


def test_get_options():
    class Config(OptionsHolder):
        default_options: ClassVar[CompleteOptions] = OptionsHolder.default_options.copy()
        default_options['keep_break'] = True

    obj = Config()
    assert obj.keep_break is True
    assert obj.get_option('keep_break') is True
    assert obj.get_option('keep_break', False) is False

    obj = Config(delete='abc')
    assert obj.get_option('delete') == 'abc'
    assert obj.get_option('delete', 'unused') == 'abc'


def test_set_option():
    obj = OptionsHolder()

    assert 'delete' not in obj.options
    assert obj.delete == ()
    obj.set_option('delete', 'abc')

    assert 'delete' in obj.options
    assert obj.delete == 'abc'
    assert obj.get_option('delete') == 'abc'
    assert obj.get_option('delete', 'unused') == 'abc'


@pytest.mark.parametrize('option_name', list(Options.__annotations__))
def test_property_implementation(option_name: OptionName) -> None:
    """Test that the implementation is correct and do not have typos."""
    obj = OptionsHolder()

    descriptor = obj.__class__.__dict__.get(option_name)
    assert isinstance(descriptor, property)

    # make sure that the docstring is correct
    assert descriptor.__doc__ == f'See :attr:`Options.{option_name}`.'

    assert descriptor.fget is not None
    assert descriptor.fget.__doc__ == descriptor.__doc__
    assert descriptor.fget.__name__ == option_name

    assert descriptor.fset is not None
    assert descriptor.fset.__doc__ in (None, '')
    assert descriptor.fset.__name__ == option_name

    assert descriptor.fdel is None  # no deleter

    # assert that the default value being returned is the correct one
    default_value = obj.__class__.default_options[option_name]
    assert descriptor.fget(obj) is default_value
    assert obj.get_option(option_name) is default_value

    # assert that the setter is correctly implemented
    descriptor.fset(obj, val := object())
    assert descriptor.fget(obj) is val
    assert obj.get_option(option_name) is val
