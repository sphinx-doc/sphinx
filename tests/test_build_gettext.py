# -*- coding: utf-8 -*-
"""
    test_build_gettext
    ~~~~~~~~~~~~~~~~~~

    Test the build process with gettext builder with the test root.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import gettext
import os
from subprocess import Popen, PIPE

from util import *
from util import SkipTest


def teardown_module():
    (test_root / '_build').rmtree(True)


@with_app(buildername='gettext')
def test_all(app):
    # Generic build; should fail only when the builder is horribly broken.
    app.builder.build_all()


@with_app(buildername='gettext')
def test_build(app):
    # Do messages end up in the correct location?
    app.builder.build(['extapi', 'subdir/includes'])
    # top-level documents end up in a message catalog
    assert (app.outdir / 'extapi.pot').isfile()
    # directory items are grouped into sections
    assert (app.outdir / 'subdir.pot').isfile()


@with_app(buildername='gettext')
def test_gettext(app):
    app.builder.build(['markup'])

    (app.outdir / 'en' / 'LC_MESSAGES').makedirs()
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['msginit', '--no-translator', '-i', 'markup.pot',
                       '--locale', 'en_US'],
                        stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely msginit was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                assert False, 'msginit exited with return code %s' % \
                        p.returncode
        assert (app.outdir / 'en_US.po').isfile(), 'msginit failed'
        try:
            p = Popen(['msgfmt', 'en_US.po', '-o',
                os.path.join('en', 'LC_MESSAGES', 'test_root.mo')],
                stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely msgfmt was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                assert False, 'msgfmt exited with return code %s' % \
                        p.returncode
        assert (app.outdir / 'en' / 'LC_MESSAGES' / 'test_root.mo').isfile(), \
                'msgfmt failed'
    finally:
        os.chdir(cwd)

    _ = gettext.translation('test_root', app.outdir, languages=['en']).gettext
    assert _("Testing various markup") == u"Testing various markup"
