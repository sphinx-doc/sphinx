# -*- coding: utf-8 -*-
"""
    test_build_gettext
    ~~~~~~~~~~~~~~~~

    Test the build process with gettext builder with the test root.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import *


def teardown_module():
    (test_root / '_build').rmtree(True)


@with_app(buildername='gettext', cleanenv=True)
def test_gettext(app):
    app.builder.build_all()
    assert (app.outdir / 'contents.pot').isfile()
    # group into sections
    assert (app.outdir / 'subdir.pot').isfile()
