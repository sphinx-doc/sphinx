# for py34 or above
from functools import partialmethod


class Cell(object):
    """An example for partialmethod.

    refs: https://docs.python.jp/3/library/functools.html#functools.partialmethod
    """

    def set_state(self, state):
        """Update state of cell to *state*."""

    #: Make a cell alive.
    set_alive = partialmethod(set_state, True)

    # a partialmethod with no docstring
    set_dead = partialmethod(set_state, False)
