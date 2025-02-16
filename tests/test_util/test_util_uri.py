from __future__ import annotations

from sphinx.util._uri import encode_uri


def test_encode_uri() -> None:
    expected = (
        'https://ru.wikipedia.org/wiki/%D0%A1%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0_'
        '%D1%83%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D1%8F_'
        '%D0%B1%D0%B0%D0%B7%D0%B0%D0%BC%D0%B8_%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D1%85'
    )
    uri = 'https://ru.wikipedia.org/wiki/Система_управления_базами_данных'
    assert encode_uri(uri) == expected

    expected = (
        'https://github.com/search?utf8=%E2%9C%93&q=is%3Aissue+is%3Aopen+is%3A'
        'sprint-friendly+user%3Ajupyter&type=Issues&ref=searchresults'
    )
    uri = (
        'https://github.com/search?utf8=✓&q=is%3Aissue+is%3Aopen+is%3A'
        'sprint-friendly+user%3Ajupyter&type=Issues&ref=searchresults'
    )
    assert encode_uri(uri) == expected
