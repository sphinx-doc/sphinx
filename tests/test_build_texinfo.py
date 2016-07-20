# -*- coding: utf-8 -*-
"""
    test_build_texinfo
    ~~~~~~~~~~~~~~~~~~

    Test the build process with Texinfo builder with the test root.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
from subprocess import Popen, PIPE

from six import PY3

from sphinx.writers.texinfo import TexinfoTranslator

from util import SkipTest, remove_unicode_literals, with_app, strip_escseq
from test_build_html import ENV_WARNINGS


TEXINFO_WARNINGS = ENV_WARNINGS + """\
%(root)s/index.rst:\\d+: WARNING: unknown option: &option
%(root)s/index.rst:\\d+: WARNING: citation not found: missing
%(root)s/index.rst:\\d+: WARNING: no matching candidate for image URI u'foo.\\*'
%(root)s/index.rst:\\d+: WARNING: no matching candidate for image URI u'svgimg.\\*'
"""

if PY3:
    TEXINFO_WARNINGS = remove_unicode_literals(TEXINFO_WARNINGS)


@with_app(buildername='texinfo', testroot='warnings', freshenv=True)
def test_texinfo_warnings(app, status, warning):
    app.builder.build_all()
    warnings = strip_escseq(warning.getvalue().replace(os.sep, '/'))
    warnings_exp = TEXINFO_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(warnings_exp + '$', warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + warnings_exp + \
        '--- Got:\n' + warnings


@with_app(buildername='texinfo')
def test_texinfo(app, status, warning):
    TexinfoTranslator.ignore_missing_images = True
    app.builder.build_all()
    # now, try to run makeinfo over it
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['makeinfo', '--no-split', 'SphinxTests.texi'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:
            raise SkipTest  # most likely makeinfo was not found
        else:
            stdout, stderr = p.communicate()
            retcode = p.returncode
            if retcode != 0:
                print(stdout)
                print(stderr)
                assert False, 'makeinfo exited with return code %s' % retcode
    finally:
        os.chdir(cwd)
