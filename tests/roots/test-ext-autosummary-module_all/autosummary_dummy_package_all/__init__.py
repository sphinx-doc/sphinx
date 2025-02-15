from .autosummary_dummy_module import Bar, PublicBar, foo, public_foo


def baz() -> None:
    """Baz function"""
    pass


def public_baz() -> None:
    """Public Baz function"""


__all__ = ['PublicBar', 'public_foo', 'public_baz', 'extra_dummy_module']  # NoQA: F822
