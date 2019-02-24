def deco1(func):
    """docstring for deco1"""
    def wrapper():
        return func()

    return wrapper


def deco2(condition, message):
    """docstring for deco2"""
    def decorator(func):
        def wrapper():
            return func()

        return wrapper
    return decorator
