class foo:
    """Demo class whose property name collides with the class name."""

    def __init__(self):
        self._value = 'hello'

    @property
    def foo(self):
        """Property docstring you expect autosummary/autodoc to show."""
        return self._value
