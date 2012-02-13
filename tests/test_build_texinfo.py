# -*- coding: utf-8 -*-
"""
    test_build_texinfo
    ~~~~~~~~~~~~~~~~~~

    Test the build process with Texinfo builder with the test root.

    :copyright: Copyright 2007-2011 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import os
import re
import sys
from StringIO import StringIO
from subprocess import Popen, PIPE

from sphinx.writers.texinfo import TexinfoTranslator

from util import *
from test_build_html import ENV_WARNINGS


def teardown_module():
    (test_root / '_build').rmtree(True)


texinfo_warnfile = StringIO()

TEXINFO_WARNINGS = ENV_WARNINGS + """\
None:None: WARNING: no matching candidate for image URI u'foo.\\*'
None:None: WARNING: no matching candidate for image URI u'svgimg.\\*'
"""

if sys.version_info >= (3, 0):
    TEXINFO_WARNINGS = remove_unicode_literals(TEXINFO_WARNINGS)


@with_app(buildername='texinfo', warning=texinfo_warnfile, cleanenv=True)
def test_texinfo(app):
    TexinfoTranslator.ignore_missing_images = True
    app.builder.build_all()
    texinfo_warnings = texinfo_warnfile.getvalue().replace(os.sep, '/')
    texinfo_warnings_exp = TEXINFO_WARNINGS % {'root': re.escape(app.srcdir)}
    assert re.match(texinfo_warnings_exp + '$', texinfo_warnings), \
           'Warnings don\'t match:\n' + \
           '--- Expected (regex):\n' + texinfo_warnings_exp + \
           '--- Got:\n' + texinfo_warnings
    # now, try to run makeinfo over it
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['makeinfo', '--no-split', 'SphinxTests.texi'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:
            pass  # most likely makeinfo was not found
        else:
            stdout, stderr = p.communicate()
            retcode = p.returncode
            if retcode != 0:
                print stdout
                print stderr
                del app.cleanup_trees[:]
                assert False, 'makeinfo exited with return code %s' % retcode
    finally:
        os.chdir(cwd)
