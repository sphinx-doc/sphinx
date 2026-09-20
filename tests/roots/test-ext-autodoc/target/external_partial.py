from functools import partial

from .partialfunction import func1

local_partial = partial(func1, 1)
