# -*- coding: utf-8 -*-
"""
    test_build_applehelp
    ~~~~~~~~~~~~~~~~~~~~

    Test the Apple Help builder and check its output.  We don't need to
    test the HTML itself; that's already handled by
    :file:`test_build_html.py`.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import plistlib

from util import with_app
from path import path

# Use plistlib.load in 3.4 and above
try:
    read_plist = plistlib.load
except AttributeError:
    read_plist = plistlib.readPlist


def check_structure(outdir):
    contentsdir = outdir / 'Contents'
    assert contentsdir.isdir()
    assert (contentsdir / 'Info.plist').isfile()

    with open(contentsdir / 'Info.plist', 'rb') as f:
        plist = read_plist(f)
    assert plist
    assert len(plist)
    assert plist.get('CFBundleIdentifier', None) == 'org.sphinx-doc.Sphinx.help'

    assert (contentsdir / 'Resources').isdir()
    assert (contentsdir / 'Resources' / 'en.lproj').isdir()


def check_localization(outdir):
    lprojdir = outdir / 'Contents' / 'Resources' / 'en.lproj'
    assert (lprojdir / 'localized.txt').isfile()


@with_app(buildername='applehelp', testroot='basic', srcdir='applehelp_output',
          confoverrides={'applehelp_bundle_id': 'org.sphinx-doc.Sphinx.help',
                         'applehelp_disable_external_tools': True})
def test_applehelp_output(app, status, warning):
    (app.srcdir / 'en.lproj').makedirs()
    (app.srcdir / 'en.lproj' / 'localized.txt').write_text('')
    app.builder.build_all()

    # Have to use bundle_path, not outdir, because we alter the latter
    # to point to the lproj directory so that the HTML arrives in the
    # correct location.
    bundle_path = path(app.builder.bundle_path)
    check_structure(bundle_path)
    check_localization(bundle_path)
