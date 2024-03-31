from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx.testing._matcher.options import DEFAULT_OPTIONS, CompleteOptions, Options
from sphinx.testing.matcher import LineMatcher

if TYPE_CHECKING:
    from collections.abc import Mapping

    from sphinx.testing._matcher.options import OptionName


def test_options_class():
    # ensure that the classes are kept synchronized
    missing_keys = Options.__annotations__.keys() - CompleteOptions.__annotations__
    assert not missing_keys, f'missing fields in proxy class: {", ".join(missing_keys)}'

    foreign_keys = CompleteOptions.__annotations__.keys() - Options.__annotations__
    assert not missing_keys, f'foreign fields in proxy class: {", ".join(foreign_keys)}'


@pytest.mark.parametrize('options', [DEFAULT_OPTIONS, LineMatcher('').options])
def test_matcher_default_options(options: Mapping[str, object]) -> None:
    """Check the synchronization of default options and classes in Sphinx."""
    processed = set()

    def check(option: OptionName, default: object) -> None:
        assert option in options
        assert options[option] == default
        processed.add(option)

    check('color', False)
    check('ctrl', True)

    check('strip', True)
    check('stripline', False)

    check('keepends', False)
    check('empty', True)
    check('compress', False)
    check('unique', False)

    check('delete', ())
    check('ignore', None)

    check('flavor', 'none')

    # check that there are no left over options
    assert sorted(processed) == sorted(Options.__annotations__)
