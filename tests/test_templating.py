# -*- coding: utf-8 -*-
"""
    test_templating
    ~~~~~~~~~~~~~~~~

    Test templating.

    :copyright: Copyright 2007-2017 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest


@pytest.mark.sphinx('html', testroot='templating')
def test_layout_overloading(app, status, warning):
    app.builder.build_update()

    result = (app.outdir / 'contents.html').text(encoding='utf-8')

    assert '<!-- layout overloading -->' in result


@pytest.mark.sphinx('html', testroot='templating')
def test_autosummary_class_template_overloading(app, status, warning):
    app.builder.build_update()

    result = (app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html').text(
        encoding='utf-8')

    assert 'autosummary/class.rst method block overloading' in result
