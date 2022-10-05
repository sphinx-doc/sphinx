"""Test templating."""

import pytest

from sphinx.ext.autosummary.generate import setup_documenters


@pytest.mark.sphinx('html', testroot='templating')
def test_layout_overloading(make_app, app_params):
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    setup_documenters(app)
    app.builder.build_update()

    result = (app.outdir / 'index.html').read_text(encoding='utf8')
    assert '<!-- layout overloading -->' in result


@pytest.mark.sphinx('html', testroot='templating')
def test_autosummary_class_template_overloading(make_app, app_params):
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    setup_documenters(app)
    app.builder.build_update()

    result = (app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html').read_text(encoding='utf8')
    assert 'autosummary/class.rst method block overloading' in result
    assert 'foobar' not in result


@pytest.mark.sphinx('html', testroot='templating',
                    confoverrides={'autosummary_context': {'sentence': 'foobar'}})
def test_autosummary_context(make_app, app_params):
    args, kwargs = app_params
    app = make_app(*args, **kwargs)
    setup_documenters(app)
    app.builder.build_update()

    result = (app.outdir / 'generated' / 'sphinx.application.TemplateBridge.html').read_text(encoding='utf8')
    assert 'autosummary/class.rst method block overloading' in result
    assert 'foobar' in result
