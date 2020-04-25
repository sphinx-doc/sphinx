# for py32 or above
from functools import lru_cache


@lru_cache(maxsize=None)
def slow_function(message, timeout):
    """This function is slow."""
    print(message)
