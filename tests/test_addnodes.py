"""Test the non-trivial features in the :mod:`sphinx.addnodes` module."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from sphinx import addnodes

if TYPE_CHECKING:
    from collections.abc import Iterator


@pytest.fixture
def sig_elements() -> Iterator[set[type[addnodes.desc_sig_element]]]:
    """Fixture returning the current ``addnodes.SIG_ELEMENTS`` set."""
    original = addnodes.SIG_ELEMENTS.copy()  # safe copy of the current nodes
    yield {*addnodes.SIG_ELEMENTS}  # temporary value to use during tests
    addnodes.SIG_ELEMENTS = original  # restore the previous value


def test_desc_sig_element_nodes(
    sig_elements: set[type[addnodes.desc_sig_element]],
) -> None:
    """Test the registration of ``desc_sig_element`` subclasses."""
    # expected desc_sig_* node classes (must be declared *after* reloading
    # the module since otherwise the objects are not the correct ones)
    EXPECTED_SIG_ELEMENTS = {
        addnodes.desc_sig_space,
        addnodes.desc_sig_name,
        addnodes.desc_sig_operator,
        addnodes.desc_sig_punctuation,
        addnodes.desc_sig_keyword,
        addnodes.desc_sig_keyword_type,
        addnodes.desc_sig_literal_number,
        addnodes.desc_sig_literal_string,
        addnodes.desc_sig_literal_char,
    }

    assert addnodes.SIG_ELEMENTS == EXPECTED_SIG_ELEMENTS

    # create a built-in custom desc_sig_element (added to SIG_ELEMENTS)
    class BuiltInSigElementLikeNode(addnodes.desc_sig_element, _sig_element=True):
        pass

    # create a custom desc_sig_element (implicitly not added to SIG_ELEMENTS)
    class Custom1SigElementLikeNode(addnodes.desc_sig_element):
        pass

    # create a custom desc_sig_element (explicitly not added to SIG_ELEMENTS)
    class Custom2SigElementLikeNode(addnodes.desc_sig_element, _sig_element=False):
        pass

    assert BuiltInSigElementLikeNode in addnodes.SIG_ELEMENTS
    assert Custom1SigElementLikeNode not in addnodes.SIG_ELEMENTS
    assert Custom2SigElementLikeNode not in addnodes.SIG_ELEMENTS
