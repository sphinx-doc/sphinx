from __future__ import annotations

from typing import TYPE_CHECKING

from sphinx.testing._matcher.options import CompleteOptions, Configurable, Options

if TYPE_CHECKING:
    from sphinx.testing._matcher.options import OptionName


def test_options_class():
    # ensure that the classes are kept synchronized
    missing_keys = Options.__annotations__.keys() - CompleteOptions.__annotations__
    assert not missing_keys, f'missing option(s): {", ".join(missing_keys)}'

    foreign_keys = CompleteOptions.__annotations__.keys() - Options.__annotations__
    assert not foreign_keys, f'unknown option(s): {", ".join(foreign_keys)}'


def test_matcher_default_options():
    """Check the synchronization of default options and classes in Sphinx."""
    default_options = Configurable.default_options.copy()

    processed = set()

    def check(option: OptionName, default: object) -> None:
        assert option not in processed
        assert option in default_options
        assert default_options[option] == default
        processed.add(option)

    check('keep_ansi', True)

    check('strip', False)
    check('stripline', False)

    check('keepends', False)
    check('keep_empty', True)
    check('compress', False)
    check('unique', False)

    check('delete', ())
    check('ignore', None)

    check('flavor', 'none')

    # check that there are no leftover options
    assert sorted(processed) == sorted(Options.__annotations__)
