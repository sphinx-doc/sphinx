# -*- coding: utf-8 -*-
"""
    test_correct_year
    ~~~~~~~~~~~~~~~~~

    Test copyright year adjustment

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
import os

from util import TestApp


def test_correct_year():
    try:
        # save current value of SOURCE_DATE_EPOCH
        sde = os.environ.pop('SOURCE_DATE_EPOCH', None)

        # test with SOURCE_DATE_EPOCH unset: no modification
        app = TestApp(buildername='html', testroot='correct-year')
        app.builder.build_all()
        content = (app.outdir / 'contents.html').text()
        app.cleanup()
        assert '2006-2009' in content

        # test with SOURCE_DATE_EPOCH set: copyright year should be
        # updated
        os.environ['SOURCE_DATE_EPOCH'] = "1293840000"
        app = TestApp(buildername='html', testroot='correct-year')
        app.builder.build_all()
        content = (app.outdir / 'contents.html').text()
        app.cleanup()
        assert '2006-2011' in content

        os.environ['SOURCE_DATE_EPOCH'] = "1293839999"
        app = TestApp(buildername='html', testroot='correct-year')
        app.builder.build_all()
        content = (app.outdir / 'contents.html').text()
        app.cleanup()
        assert '2006-2010' in content

    finally:
        # Restores SOURCE_DATE_EPOCH
        if sde is None:
            os.environ.pop('SOURCE_DATE_EPOCH', None)
        else:
            os.environ['SOURCE_DATE_EPOCH'] = sde
