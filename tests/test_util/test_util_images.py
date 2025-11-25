"""Test images util."""

from __future__ import annotations

import pytest

from sphinx.util.images import (
    get_image_extension,
    get_image_size,
    guess_mimetype,
    parse_data_uri,
)

TYPE_CHECKING = False
if TYPE_CHECKING:
    from pathlib import Path

GIF_FILENAME = 'img.gif'
PNG_FILENAME = 'img.png'
PDF_FILENAME = 'img.pdf'
TXT_FILENAME = 'index.txt'


def test_get_image_size(rootdir: Path) -> None:
    assert get_image_size(rootdir / 'test-root' / GIF_FILENAME) == (200, 181)
    assert get_image_size(rootdir / 'test-root' / PNG_FILENAME) == (200, 181)
    assert get_image_size(rootdir / 'test-root' / PDF_FILENAME) is None
    assert get_image_size(rootdir / 'test-root' / TXT_FILENAME) is None


@pytest.mark.filterwarnings('ignore:The content argument')
def test_guess_mimetype() -> None:
    # guess by filename
    assert guess_mimetype('img.png') == 'image/png'
    assert guess_mimetype('img.jpg') == 'image/jpeg'
    assert guess_mimetype('img.txt') is None
    assert guess_mimetype('img.txt', default='text/plain') == 'text/plain'
    assert guess_mimetype('no_extension') is None
    assert guess_mimetype('IMG.PNG') == 'image/png'

    # default parameter is used when no extension
    assert guess_mimetype('img.png', 'text/plain') == 'image/png'
    assert guess_mimetype('no_extension', 'text/plain') == 'text/plain'


def test_get_image_extension() -> None:
    assert get_image_extension('image/png') == '.png'
    assert get_image_extension('image/jpeg') == '.jpg'
    assert get_image_extension('image/svg+xml') == '.svg'
    assert get_image_extension('text/plain') is None


def test_parse_data_uri() -> None:
    # standard case
    uri = (
        'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4'
        '//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=='
    )
    image = parse_data_uri(uri)
    assert image is not None
    assert image.mimetype == 'image/png'
    assert image.charset == 'US-ASCII'

    # no mimetype
    uri = (
        'data:charset=utf-8,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElE'
        'QVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=='
    )
    image = parse_data_uri(uri)
    assert image is not None
    assert image.mimetype == 'text/plain'
    assert image.charset == 'utf-8'

    # non data URI
    uri = (
        'image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4'
        '//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=='
    )
    image = parse_data_uri(uri)
    assert image is None

    # invalid data URI (no properties)
    uri = (
        'data:iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4'
        '//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=='
    )
    with pytest.raises(ValueError, match=r'malformed data URI'):
        parse_data_uri(uri)

    # not base64
    uri = (
        'data:image/svg+xml,%3Csvg%20width%3D%22100%22%20height%3D%22100%22%20'
        'xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%3E%3Ccircle%20cx'
        '%3D%2250%22%20cy%3D%2250%22%20r%3D%2240%22%20fill%3D%22blue%22%2F%3E'
        '%3C%2Fsvg%3E'
    )
    image = parse_data_uri(uri)
    assert image is not None
    assert image.mimetype == 'image/svg+xml'
    assert b'%' not in image.data
