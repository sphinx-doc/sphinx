from sphinx.util.jsdump import dumps, loads


def test_jsdump():
    data = {'1a': 1}
    assert dumps(data) == '{"1a":1}'
    assert data == loads(dumps(data))

    data = {'a1': 1}
    assert dumps(data) == '{a1:1}'
    assert data == loads(dumps(data))

    data = {'a\xe8': 1}
    assert dumps(data) == '{"a\\u00e8":1}'
    assert data == loads(dumps(data))

    data = {'_foo': 1}
    assert dumps(data) == '{_foo:1}'
    assert data == loads(dumps(data))
