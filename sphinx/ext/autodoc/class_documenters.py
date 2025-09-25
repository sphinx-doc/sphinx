from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from sphinx.ext.autodoc.documenter_base import Documenter
from sphinx.util.typing import OptionSpec

if TYPE_CHECKING:
    from sphinx.ext.autodoc._property_types import _ClassDefProperties


class ClassDocumenter(Documenter):
    """Specialized Documenter subclass for classes."""

    props: _ClassDefProperties

    objtype = 'class'
    member_order = 20
    option_spec: ClassVar[OptionSpec] = {
        'members': True,
        'undoc-members': False,
        'no-index': False,
        'no-index-entry': False,
        'inherited-members': False,
        'show-inheritance': False,
        'private-members': None,
        'special-members': None,
        'exclude-members': [],
        'member-order': 'alphabetical',
        'noindex': False,
    }

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.options = self.options.merge_member_options()

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return inspect.isclass(member)

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add inheritance info if enabled
        if self.options.show_inheritance:
            if hasattr(self.object, '__bases__'):
                bases = [base.__name__ for base in self.object.__bases__ if base is not object]
                if bases:
                    self.add_line(f'   Bases: {", ".join(bases)}', sourcename)

    def document_members(self, want_all: bool = True, **kwargs: Any) -> None:
        """Generate reST for the members of the class."""
        want_all, selected = self.filter_members(
            self.get_object_members(want_all, **kwargs), want_all
        )
        if not want_all and not selected:
            return

        # process the selected members
        for name, (isattr, value) in selected:
            self.document_member(name, isattr, value)

    def document_member(self, name: str, isattr: bool, value: Any) -> None:
        """Document a single member."""
        classes = self.documenters
        for documenter_cls in classes.values():
            if documenter_cls.can_document_member(value, name, isattr, self):
                documenter = documenter_cls(self.directive, name, self.indent)
                documenter.generate()
                break


class ExceptionDocumenter(ClassDocumenter):
    """Specialized Documenter subclass for exceptions."""

    objtype = 'exception'
    member_order = 30

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return (
            inspect.isclass(member)
            and issubclass(member, BaseException)
            and member is not BaseException
        )


# Define __all__ for this module
__all__ = ['ClassDocumenter', 'ExceptionDocumenter']
