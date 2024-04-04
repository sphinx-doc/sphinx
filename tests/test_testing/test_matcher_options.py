from __future__ import annotations

from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

from sphinx.testing._matcher.options import CompleteOptions, Options, OptionsHolder

if TYPE_CHECKING:
    from typing import ClassVar

    from sphinx.testing._matcher.options import OptionName


def test_options_class():
    assert len(Options.__annotations__) > 0, 'missing annotations'

    # ensure that the classes are kept synchronized
    missing_keys = Options.__annotations__.keys() - CompleteOptions.__annotations__
    assert not missing_keys, f'missing option(s): {", ".join(missing_keys)}'

    foreign_keys = CompleteOptions.__annotations__.keys() - Options.__annotations__
    assert not foreign_keys, f'unknown option(s): {", ".join(foreign_keys)}'

    for name in Options.__annotations__:
        func = OptionsHolder.__dict__.get(name)
        assert isinstance(func, property), f'missing property for option {name!r}'
        assert func.fget is not None, f'missing getter for option {name!r}'
        assert func.fset is not None, f'missing setter for option {name!r}'
        assert func.fdel is None, f'extra deleter for option {name!r}'


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


def test_get_option():
    class Config(OptionsHolder):
        default_options: ClassVar[CompleteOptions] = OptionsHolder.default_options.copy()
        default_options['keep_break'] = True

    obj = Config()
    assert isinstance(obj.options, MappingProxyType)

    assert 'keep_break' not in obj.options
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


@pytest.mark.parametrize('option', list(Options.__annotations__))
def test_set_option_property_implementation(option: OptionName) -> None:
    """Test that the implementation is correct and do not have typos."""
    obj, val = OptionsHolder(), object()  # fresh sentinel for every option
    # assert that the default value being returned is the correct one
    assert obj.__class__.__dict__[option].fget(obj) is OptionsHolder.default_options[option]
    obj.__class__.__dict__[option].fset(obj, val)
    assert obj.get_option(option) is val
    assert obj.__class__.__dict__[option].fget(obj) is val
