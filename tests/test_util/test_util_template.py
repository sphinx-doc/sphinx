"""Tests sphinx.util.template functions."""

from sphinx.util.template import ReSTRenderer


def test_ReSTRenderer_escape():
    r = ReSTRenderer()
    template = '{{ "*hello*" | e }}'
    assert r.render_string(template, {}) == r'\*hello\*'


def test_ReSTRenderer_heading():
    r = ReSTRenderer()

    template = '{{ "hello" | heading }}'
    assert r.render_string(template, {}) == 'hello\n====='

    template = '{{ "hello" | heading(1) }}'
    assert r.render_string(template, {}) == 'hello\n====='

    template = '{{ "русский язык" | heading(2) }}'
    assert r.render_string(template, {}) == 'русский язык\n------------'

    # language: ja
    r.env.language = 'ja'
    template = '{{ "русский язык" | heading }}'
    assert r.render_string(template, {}) == 'русский язык\n======================='
