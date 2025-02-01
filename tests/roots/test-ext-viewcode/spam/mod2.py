"""mod2"""


def decorator(f):
    return f


@decorator
def func2(a, b):
    """this is func2"""
    return a, b


@decorator
class Class2:
    """this is Class2"""
