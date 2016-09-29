# -*- coding: utf-8 -*-
"""
    test_util_rst
    ~~~~~~~~~~~~~~~

    Tests sphinx.util.rst functions.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from sphinx.util.rst import escape


def test_escape():
    assert escape(':ref:`id`') == '\:ref\:\`id\`'
    assert escape('footnote [#]_') == 'footnote \[\#\]\_'
