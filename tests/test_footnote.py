# -*- coding: utf-8 -*-
"""
    test_footnote
    ~~~~~~~~~~~~~

    Test for footnote and citation.

    :copyright: Copyright 2007-2013 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

from util import test_root, with_app


def teardown_module():
    (test_root / '_build').rmtree(True)


@with_app(buildername='html')
def test_html(app):
    app.builder.build(['footnote'])
    result = (app.outdir / 'footnote.html').text(encoding='utf-8')
    expects = [
        '<a class="footnote-reference" href="#id5" id="id1">[1]</a>',
        '<a class="footnote-reference" href="#id6" id="id2">[2]</a>',
        '<a class="footnote-reference" href="#foo" id="id3">[3]</a>',
        '<a class="reference internal" href="#bar" id="id4">[bar]</a>',
        '<a class="fn-backref" href="#id1">[1]</a>',
        '<a class="fn-backref" href="#id2">[2]</a>',
        '<a class="fn-backref" href="#id3">[3]</a>',
        '<a class="fn-backref" href="#id4">[bar]</a>',
        ]
    for expect in expects:
        matches = re.findall(re.escape(expect), result)
        assert len(matches) == 1
