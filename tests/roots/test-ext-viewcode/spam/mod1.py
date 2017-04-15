"""
mod1
"""

def decorator(f):
    return f

@decorator
def func1(a, b):
    """
    this is func1
    """
    return a, b


@decorator
class Class1(object):
    """
    this is Class1
    """
