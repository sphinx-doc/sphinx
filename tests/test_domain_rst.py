"""
    test_rst_domain
    ~~~~~~~~~~~~~~~

    Tests the reStructuredText domain.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.domains.rst import parse_directive


def test_parse_directive():
    s = parse_directive(' foö  ')
    assert s == ('foö', '')

    s = parse_directive(' ..    foö ::  ')
    assert s == ('foö', ' ')

    s = parse_directive('.. foö:: args1 args2')
    assert s == ('foö', ' args1 args2')

    s = parse_directive('.. :: bar')
    assert s == ('.. :: bar', '')
