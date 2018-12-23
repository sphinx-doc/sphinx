"""
    test_build_htmlhelp
    ~~~~~~~~~~~~~~~~~~~
    Test the HTML Help builder and check output against XPath.
    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

import pytest


@pytest.mark.sphinx('htmlhelp', testroot='build-htmlhelp')
def test_chm(app):
    app.build()

    # check .hhk file
    outname = app.builder.config.htmlhelp_basename
    hhk_path = str(app.outdir / outname + '.hhk')

    with open(hhk_path, 'rb') as f:
        data = f.read()
    m = re.search(br'&#[xX][0-9a-fA-F]+;', data)
    assert m == None, 'Hex escaping exists in .hhk file: ' + str(m.group(0))

