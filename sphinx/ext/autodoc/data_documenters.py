from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from sphinx.ext.autodoc.documenter_base import Documenter
from sphinx.util.typing import OptionSpec

if TYPE_CHECKING:
    from sphinx.ext.autodoc._property_types import _AssignStatementProperties


class DataDocumenter(Documenter):
    """Specialized Documenter subclass for module-level data/variables."""

    props: _AssignStatementProperties

    objtype = 'data'
    member_order = 40
    option_spec: ClassVar[OptionSpec] = {
        'no-index': False,
        'no-index-entry': False,
        'no-value': False,
        'annotation': '',
        'noindex': False,
    }

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        # Can document any variable/constant that is not a function/method/class
        return (
            not inspect.isfunction(member)
            and not inspect.ismethod(member)
            and not inspect.isclass(member)
            and not membername.startswith('_')
        )

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add annotation if specified
        if self.options.annotation:
            self.add_line(f'   :annotation: = {self.options.annotation}', sourcename)

        # add value if not suppressed
        if not self.options.no_value and self.object is not None:
            try:
                value_str = repr(self.object)
                # Truncate very long values
                if len(value_str) > 50:
                    value_str = value_str[:47] + '...'
                self.add_line(f'   = {value_str}', sourcename)
            except Exception:
                pass


class AttributeDocumenter(Documenter):
    """Specialized Documenter subclass for class attributes."""

    objtype = 'attribute'
    member_order = 60
    option_spec: ClassVar[OptionSpec] = {
        'no-index': False,
        'no-index-entry': False,
        'annotation': '',
        'noindex': False,
    }

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        # Can document class attributes (but not methods or properties)
        return (
            isattr
            and not membername.startswith('_')
            and not callable(member)
        )

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add annotation if specified
        if self.options.annotation:
            self.add_line(f'   :annotation: = {self.options.annotation}', sourcename)


class PropertyDocumenter(Documenter):
    """Specialized Documenter subclass for properties."""

    objtype = 'property'
    member_order = 60
    option_spec: ClassVar[OptionSpec] = {
        'no-index': False,
        'no-index-entry': False,
        'annotation': '',
        'noindex': False,
    }

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return isinstance(member, property)

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add annotation if specified
        if self.options.annotation:
            self.add_line(f'   :annotation: = {self.options.annotation}', sourcename)


# Define __all__ for this module
__all__ = ['DataDocumenter', 'AttributeDocumenter', 'PropertyDocumenter']
