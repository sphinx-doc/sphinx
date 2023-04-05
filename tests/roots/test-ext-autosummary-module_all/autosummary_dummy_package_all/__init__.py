from .autosummary_dummy_module import Bar, foo, public_foo, PublicBar

def baz():
    """Baz function"""
    pass


def public_baz():
    """Public Baz function"""


__all__ = ["PublicBar", "public_foo", "public_baz", "extra_dummy_module"]
