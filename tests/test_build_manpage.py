# -*- coding: utf-8 -*-
"""
    test_build_manpage
    ~~~~~~~~~~~~~~~~~~

    Test the build process with manpage builder with the test root.

    :copyright: Copyright 2007-2019 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import pytest


@pytest.mark.sphinx('man')
def test_all(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / 'SphinxTests.1').exists()

    content = (app.outdir / 'SphinxTests.1').text()
    assert r'\fBprint \fP\fIi\fP\fB\en\fP' in content
    assert r'\fBmanpage\en\fP' in content

    # term of definition list including nodes.strong
    assert '\n.B term1\n' in content
    assert '\nterm2 (\\fBstronged partially\\fP)\n' in content


@pytest.mark.sphinx('man', testroot='directive-code')
def test_captioned_code_block(app, status, warning):
    app.builder.build_all()
    content = (app.outdir / 'python.1').text()

    assert ('.sp\n'
            'caption \\fItest\\fP rb\n'
            '.INDENT 0.0\n'
            '.INDENT 3.5\n'
            '.sp\n'
            '.nf\n'
            '.ft C\n'
            'def ruby?\n'
            '    false\n'
            'end\n'
            '.ft P\n'
            '.fi\n'
            '.UNINDENT\n'
            '.UNINDENT\n' in content)
