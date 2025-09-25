from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from sphinx.ext.autodoc.documenter_base import Documenter
from sphinx.util.typing import OptionSpec

if TYPE_CHECKING:
    from sphinx.ext.autodoc._property_types import _FunctionDefProperties


class FunctionDocumenter(Documenter):
    """Specialized Documenter subclass for functions."""

    props: _FunctionDefProperties

    objtype = 'function'
    member_order = 30
    option_spec: ClassVar[OptionSpec] = {
        'no-index': False,
        'no-index-entry': False,
        'noindex': False,
    }

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return inspect.isfunction(member) or inspect.ismethod(member)

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add function signature if available
        if self.args:
            self.add_line(f'   {self.args}', sourcename)


class DecoratorDocumenter(FunctionDocumenter):
    """Specialized Documenter subclass for decorators."""

    objtype = 'decorator'
    member_order = 35

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        # Check if this is a decorator (function with __name__ ending in 'decorator')
        return (
            inspect.isfunction(member)
            and getattr(member, '__name__', '').endswith('decorator')
        )


class MethodDocumenter(Documenter):
    """Specialized Documenter subclass for methods."""

    objtype = 'method'
    member_order = 50
    option_spec: ClassVar[OptionSpec] = {
        'no-index': False,
        'no-index-entry': False,
        'noindex': False,
    }

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return inspect.ismethod(member) and not membername.startswith('_')

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add method signature if available
        if self.args:
            self.add_line(f'   {self.args}', sourcename)


# Define __all__ for this module
__all__ = ['FunctionDocumenter', 'DecoratorDocumenter', 'MethodDocumenter']
