# -*- coding: utf-8 -*-
"""
    test_build_texinfo
    ~~~~~~~~~~~~~~~~~~

    Test the build process with Texinfo builder with the test root.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import os
import re
from subprocess import Popen, PIPE

import pytest
from six import PY3
from test_build_html import ENV_WARNINGS

from sphinx.testing.util import remove_unicode_literals, strip_escseq
from sphinx.writers.texinfo import TexinfoTranslator


TEXINFO_WARNINGS = ENV_WARNINGS + """\
%(root)s/index.rst:\\d+: WARNING: unknown option: &option
%(root)s/index.rst:\\d+: WARNING: citation not found: missing
%(root)s/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: foo.\\*
%(root)s/index.rst:\\d+: WARNING: a suitable image for texinfo builder not found: \
\\['application/pdf', 'image/svg\\+xml'\\] \\(svgimg.\\*\\)
"""

if PY3:
    TEXINFO_WARNINGS = remove_unicode_literals(TEXINFO_WARNINGS)


@pytest.mark.sphinx('texinfo', testroot='warnings', freshenv=True)
def test_texinfo_warnings(app, status, warning):
    app.builder.build_all()
    warnings = strip_escseq(re.sub(re.escape(os.sep) + '{1,2}', '/', warning.getvalue()))
    warnings_exp = TEXINFO_WARNINGS % {
        'root': re.escape(app.srcdir.replace(os.sep, '/'))}
    assert re.match(warnings_exp + '$', warnings), \
        'Warnings don\'t match:\n' + \
        '--- Expected (regex):\n' + warnings_exp + \
        '--- Got:\n' + warnings


@pytest.mark.sphinx('texinfo')
def test_texinfo(app, status, warning):
    TexinfoTranslator.ignore_missing_images = True
    app.builder.build_all()
    result = (app.outdir / 'SphinxTests.texi').text(encoding='utf8')
    assert ('@anchor{markup doc}@anchor{12}'
            '@anchor{markup id1}@anchor{13}'
            '@anchor{markup testing-various-markup}@anchor{14}' in result)
    # now, try to run makeinfo over it
    cwd = os.getcwd()
    os.chdir(app.outdir)
    try:
        try:
            p = Popen(['makeinfo', '--no-split', 'SphinxTests.texi'],
                      stdout=PIPE, stderr=PIPE)
        except OSError:
            raise pytest.skip.Exception  # most likely makeinfo was not found
        else:
            stdout, stderr = p.communicate()
            retcode = p.returncode
            if retcode != 0:
                print(stdout)
                print(stderr)
                assert False, 'makeinfo exited with return code %s' % retcode
    finally:
        os.chdir(cwd)
