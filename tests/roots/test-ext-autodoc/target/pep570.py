def foo(*, a, b):
    pass

def bar(a, b, /, c, d):
    pass

def baz(a, /, *, b):
    pass

def qux(a, b, /):
    pass
