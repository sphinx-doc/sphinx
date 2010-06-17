# -*- coding: utf-8 -*-
"""
    test_build_gettext
    ~~~~~~~~~~~~~~~~

    Test the build process with gettext builder with the test root.

    :copyright: Copyright 2010 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
from subprocess import Popen, PIPE

from util import *


def teardown_module():
    (test_root / '_build').rmtree(True)


@with_app(buildername='gettext')
def test_build(app):
    app.builder.build(['extapi', 'subdir/includes'])
    # documents end up in a message catalog
    assert (app.outdir / 'extapi.pot').isfile()
    # ..and are grouped into sections
    assert (app.outdir / 'subdir.pot').isfile()

@with_app(buildername='gettext')
def test_gettext(app):
    app.builder.build(['markup'])

    (app.outdir / 'en' / 'LC_MESSAGES').makedirs()
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['msginit', '--no-translator', '-i', 'markup.pot'],
                        stdout=PIPE, stderr=PIPE)
        except OSError:
            return  # most likely msginit was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                assert False, 'msginit exited with return code %s' % p.returncode
        assert (app.outdir / 'en_US.po').isfile(), 'msginit failed'
        try:
            p = Popen(['msgfmt', 'en_US.po', '-o',
                os.path.join('en', 'LC_MESSAGES', 'test_root.mo')],
                stdout=PIPE, stderr=PIPE)
        except OSError:
            return  # most likely msgfmt was not found
        else:
            stdout, stderr = p.communicate()
            if p.returncode != 0:
                print stdout
                print stderr
                assert False, 'msgfmt exited with return code %s' % p.returncode
        assert (app.outdir / 'en' / 'LC_MESSAGES' / 'test_root.mo').isfile(), 'msgfmt failed'
    finally:
        os.chdir(cwd)
