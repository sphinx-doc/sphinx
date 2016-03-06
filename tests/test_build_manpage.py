# -*- coding: utf-8 -*-
"""
    test_build_manpage
    ~~~~~~~~~~~~~~~~~~

    Test the build process with manpage builder with the test root.

    :copyright: Copyright 2007-2016 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

from util import with_app


@with_app(buildername='man')
def test_all(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / 'SphinxTests.1').exists()

    content = (app.outdir / 'SphinxTests.1').text()
    assert r'\fBprint \fP\fIi\fP\fB\en\fP' in content
    assert r'\fBmanpage\en\fP' in content

    # term of definition list including nodes.strong
    assert '\n.B term1\n' in content
    assert '\nterm2 (\\fBstronged partially\\fP)\n' in content
