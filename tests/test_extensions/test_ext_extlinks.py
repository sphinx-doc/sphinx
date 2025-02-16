from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from sphinx.testing.util import SphinxTestApp


@pytest.mark.sphinx(
    'html',
    testroot='ext-extlinks-hardcoded-urls',
    confoverrides={'extlinks_detect_hardcoded_links': False},
)
def test_extlinks_detect_candidates(app: SphinxTestApp) -> None:
    app.build()
    assert app.warning.getvalue() == ''


@pytest.mark.sphinx('html', testroot='ext-extlinks-hardcoded-urls')
def test_replaceable_uris_emit_extlinks_warnings(app: SphinxTestApp) -> None:
    app.build()
    warning_output = app.warning.getvalue()

    # there should be exactly three warnings for replaceable URLs
    message = (
        "index.rst:%d: WARNING: hardcoded link 'https://github.com/sphinx-doc/sphinx/issues/1' "
        "could be replaced by an extlink (try using '%s' instead)"
    )
    assert message % (11, ':issue:`1`') in warning_output
    assert message % (13, ':issue:`inline replaceable link <1>`') in warning_output
    assert message % (15, ':issue:`replaceable link <1>`') in warning_output


@pytest.mark.sphinx(
    'html',
    testroot='ext-extlinks-hardcoded-urls-multiple-replacements',
)
def test_all_replacements_suggested_if_multiple_replacements_possible(
    app: SphinxTestApp,
) -> None:
    app.build()
    warning_output = app.warning.getvalue()
    # there should be six warnings for replaceable URLs, three pairs per link
    assert warning_output.count('WARNING: hardcoded link') == 6
    message = (
        "index.rst:%d: WARNING: hardcoded link 'https://github.com/octocat' "
        "could be replaced by an extlink (try using '%s' instead)"
    )
    assert message % (14, ':user:`octocat`') in warning_output
    assert message % (16, ':user:`inline replaceable link <octocat>`') in warning_output
    assert message % (18, ':user:`replaceable link <octocat>`') in warning_output
    message = (
        "index.rst:%d: WARNING: hardcoded link 'https://github.com/octocat' "
        "could be replaced by an extlink (try using '%s' instead)"
    )
    assert message % (14, ':repo:`octocat`') in warning_output
    assert message % (16, ':repo:`inline replaceable link <octocat>`') in warning_output
    assert message % (18, ':repo:`replaceable link <octocat>`') in warning_output
