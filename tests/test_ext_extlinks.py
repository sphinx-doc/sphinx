import pytest


@pytest.mark.sphinx('html', testroot='ext-extlinks-hardcoded-urls')
def test_replaceable_uris_emit_extlinks_warnings(app, warning):
    app.build()
    warning_output = warning.getvalue()
    # there should be exactly three warnings for replaceable URLs
    message = (
        "WARNING: hardcoded link 'https://github.com/sphinx-doc/sphinx/issues/1' "
        "could be replaced by an extlink (try using ':issue:`1`' instead)"
    )
    assert f"index.rst:11: {message}" in warning_output
    assert f"index.rst:13: {message}" in warning_output
    assert f"index.rst:15: {message}" in warning_output


@pytest.mark.sphinx('html', testroot='ext-extlinks-hardcoded-urls-multiple-replacements')
def test_all_replacements_suggested_if_multiple_replacements_possible(app, warning):
    app.build()
    warning_output = warning.getvalue()
    # there should be six warnings for replaceable URLs, three pairs per link
    message = (
        "WARNING: hardcoded link 'https://github.com/octocat' "
        "could be replaced by an extlink (try using ':user:`octocat`' instead)"
    )
    assert f"index.rst:14: {message}" in warning_output
    assert f"index.rst:16: {message}" in warning_output
    assert f"index.rst:18: {message}" in warning_output
    message = (
        "WARNING: hardcoded link 'https://github.com/octocat' "
        "could be replaced by an extlink (try using ':repo:`octocat`' instead)"
    )
    assert f"index.rst:14: {message}" in warning_output
    assert f"index.rst:16: {message}" in warning_output
    assert f"index.rst:18: {message}" in warning_output
