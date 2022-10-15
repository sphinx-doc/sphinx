"""Test object description directives."""

import pytest


@pytest.mark.sphinx('text', testroot='object-description-sections')
def test_object_description_sections(app):
    app.builder.build_all()
    index = (app.outdir / 'index.txt').read_text(encoding='utf8')
    assert index.split('\n') == [
        'func()',
        '',
        '',
        '   Overview',
        '   ********',
        '',
        '   Lorem ipsum dolar sit amet',
        ''
    ]
