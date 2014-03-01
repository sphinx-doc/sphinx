# -*- coding: utf-8 -*-
"""
    test_templating
    ~~~~~~~~~~~~~~~~

    Test templating.

    :copyright: Copyright 2007-2014 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from util import test_roots, with_app


def teardown_module():
    (test_roots / 'test-templating' / '_build').rmtree(True),


@with_app(buildername='html', srcdir=(test_roots / 'test-templating'))
def test_layout_overloading(app):
    app.builder.build_all()

    result = (app.outdir / 'contents.html').text(encoding='utf-8')

    assert '<!-- layout overloading -->' in result


@with_app(buildername='html', srcdir=(test_roots / 'test-templating'))
def test_autosummary_class_template_overloading(app):
    app.builder.build_all()

    result = (app.outdir / 'generated' / 'sphinx.application.Sphinx.html').text(
                encoding='utf-8')

    assert 'autosummary/class.rst method block overloading' in result

