# -*- coding: utf-8 -*-
"""
    test_rst_domain
    ~~~~~~~~~~~~~~~

    Tests the reStructuredText domain.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from sphinx.domains.rst import parse_directive


def test_parse_directive():
    s = parse_directive(u' foö  ')
    assert s == (u'foö', '')

    s = parse_directive(u' ..    foö ::  ')
    assert s == (u'foö', ' ')

    s = parse_directive(u'.. foö:: args1 args2')
    assert s == (u'foö', ' args1 args2')

    s = parse_directive('.. :: bar')
    assert s == ('.. :: bar', '')
