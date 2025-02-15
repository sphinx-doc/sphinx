from autosummary_dummy_module import Foo


class InheritedAttrClass(Foo):
    def __init__(self) -> None:
        #: other docstring
        self.subclassattr = 'subclassattr'

        super().__init__()


__all__ = ['InheritedAttrClass']
