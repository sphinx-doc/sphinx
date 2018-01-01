# -*- coding: utf-8 -*-
"""
    test_build_linkcheck
    ~~~~~~~~~~~~~~~~~~~~

    Test the build process with manpage builder with the test root.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import pytest


@pytest.mark.sphinx('linkcheck', testroot='linkcheck', freshenv=True)
def test_defaults(app, status, warning):
    app.builder.build_all()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').text()

    print(content)
    # looking for #top should fail
    assert "Anchor 'top' not found" in content
    assert len(content.splitlines()) == 1


@pytest.mark.sphinx(
    'linkcheck', testroot='linkcheck', freshenv=True,
    confoverrides={'linkcheck_anchors_ignore': ["^!", "^top$"]})
def test_anchors_ignored(app, status, warning):
    app.builder.build_all()

    assert (app.outdir / 'output.txt').exists()
    content = (app.outdir / 'output.txt').text()

    # expect all ok when excluding #top
    assert not content
