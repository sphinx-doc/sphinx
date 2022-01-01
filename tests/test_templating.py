"""
    test_templating
    ~~~~~~~~~~~~~~~~

    Test templating.

    :copyright: Copyright 2007-2022 by the Sphinx team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import pytest

from sphinx.ext.autosummary.generate import setup_documenters


@pytest.mark.sphinx('html', testroot='templating')
def test_layout_overloading(make_app, app_params):
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    setup_documenters(app)
    app.builder.build_update()

    result = (app.outdir / 'index.html').read_text()
    assert '<!-- layout overloading -->' in result


@pytest.mark.sphinx('html', testroot='templating')
def test_autosummary_class_template_overloading(make_app, app_params):
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    setup_documenters(app)
    app.builder.build_update()

    result = (app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html').read_text()
    assert 'autosummary/class.rst method block overloading' in result
    assert 'foobar' not in result


@pytest.mark.sphinx('html', testroot='templating',
                    confoverrides={'autosummary_context': {'sentence': 'foobar'}})
def test_autosummary_context(make_app, app_params):
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    setup_documenters(app)
    app.builder.build_update()

    result = (app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html').read_text()
    assert 'autosummary/class.rst method block overloading' in result
    assert 'foobar' in result
