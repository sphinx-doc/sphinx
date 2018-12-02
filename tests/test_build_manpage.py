# -*- coding: utf-8 -*-
"""
    test_build_manpage
    ~~~~~~~~~~~~~~~~~~

    Test the build process with manpage builder with the test root.

    :copyright: Copyright 2007-2018 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""
from __future__ import print_function

import pytest

from sphinx.builders.manpage import default_man_pages
from sphinx.config import Config


@pytest.mark.sphinx('man')
def test_all(app, status, warning):
    app.builder.build_all()
    assert (app.outdir / 'sphinxtests.1').exists()

    content = (app.outdir / 'sphinxtests.1').text()
    assert r'\fBprint \fP\fIi\fP\fB\en\fP' in content
    assert r'\fBmanpage\en\fP' in content

    # term of definition list including nodes.strong
    assert '\n.B term1\n' in content
    assert '\nterm2 (\\fBstronged partially\\fP)\n' in content


def test_default_man_pages():
    config = Config({'master_doc': 'index',
                     'project': u'STASI™ Documentation',
                     'author': u"Wolfgang Schäuble & G'Beckstein",
                     'release': '1.0'})
    config.init_values()
    expected = [('index', 'stasi', u'STASI™ Documentation 1.0',
                 [u"Wolfgang Schäuble & G'Beckstein"], 1)]
    assert default_man_pages(config) == expected
