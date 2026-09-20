"""Test the AnchorCheckParser class."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest import mock

from sphinx.builders.linkcheck import AnchorCheckParser, contains_anchor

if TYPE_CHECKING:
    from typing import Any


def test_anchor_check_parser_basic() -> None:
    """Test basic anchor matching functionality."""
    parser = AnchorCheckParser('test-anchor')
    parser.feed('<html><body><div id="test-anchor">Test</div></body></html>')
    assert parser.found is True

    parser = AnchorCheckParser('non-existent')
    parser.feed('<html><body><div id="test-anchor">Test</div></body></html>')
    assert parser.found is False


def test_anchor_check_parser_with_encoded_anchors() -> None:
    """Test anchor matching with encoded characters."""
    # Test with encoded slash
    parser = AnchorCheckParser(
        'standard-input/output-stdio', 'standard-input%2Foutput-stdio'
    )
    parser.feed(
        '<html><body><div id="standard-input%2Foutput-stdio">Test</div></body></html>'
    )
    assert parser.found is True

    # Test with plus sign
    parser = AnchorCheckParser('encoded+anchor', 'encoded%2Banchor')
    parser.feed('<html><body><div id="encoded%2Banchor">Test</div></body></html>')
    assert parser.found is True

    # Test with space
    parser = AnchorCheckParser('encoded space', 'encoded%20space')
    parser.feed('<html><body><div id="encoded%20space">Test</div></body></html>')
    assert parser.found is True


def test_contains_anchor_with_encoded_characters() -> None:
    """Test the contains_anchor function with encoded characters."""
    mock_response = mock.MagicMock()

    # Setup a response that returns HTML with encoded anchors
    def mock_iter_content(chunk_size: Any = None, decode_unicode: Any = None) -> Any:
        content = '<html><body><div id="standard-input%2Foutput-stdio">Test</div></body></html>'
        yield content

    mock_response.iter_content = mock_iter_content

    # Test with original encoded anchor
    assert (
        contains_anchor(
            mock_response,
            'standard-input/output-stdio',
            'standard-input%2Foutput-stdio',
        )
        is True
    )

    # Test with decoded anchor only
    mock_response2 = mock.MagicMock()
    mock_response2.iter_content = mock_iter_content
    assert contains_anchor(mock_response2, 'standard-input/output-stdio') is True

    # Test with non-existent anchor
    mock_response3 = mock.MagicMock()
    mock_response3.iter_content = mock_iter_content
    assert contains_anchor(mock_response3, 'non-existent-anchor') is False
