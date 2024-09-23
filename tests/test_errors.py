from sphinx.errors import ExtensionError


def test_extension_error_repr():
    exc = ExtensionError('foo')
    assert repr(exc) == "ExtensionError('foo')"


def test_extension_error_with_orig_exc_repr():
    exc = ExtensionError('foo', Exception('bar'))
    assert repr(exc) == "ExtensionError('foo', Exception('bar'))"
