# -*- coding: utf-8 -*-

def test_jsdump():
    from sphinx.util.jsdump import dumps

    assert dumps({'1a': 1}) == '{"1a":1}'
    assert dumps({'a1': 1}) == '{a1:1}'

    assert dumps({u'a\xe8': 1}) == '{"a\\u00e8":1}'
