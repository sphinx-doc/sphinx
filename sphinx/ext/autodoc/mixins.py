from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from sphinx.ext.autodoc.documenter_base import Documenter

if TYPE_CHECKING:
    from sphinx.util.inspect import Signature


class DocstringSignatureMixin:
    """Mixin for documenters that can read signatures from docstrings."""

    __docstring_signature__: ClassVar[bool] = True

    def get_docstring_signature(self) -> tuple[str, str] | None:
        """Extract signature from the first line of the docstring."""
        docstring = self.get_docstring()
        if not docstring:
            return None

        first_line = docstring[0].strip()
        if not first_line:
            return None

        # Try to extract a signature-like pattern
        import re
        sig_pattern = r'^(\w+\([^)]*\))'
        match = re.match(sig_pattern, first_line)
        if match:
            return match.group(1), '\n'.join(docstring[1:])

        return None


class ClassLevelDocumenter(Documenter):
    """Base class for documenters that document class-level objects."""

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        return cls.can_document_member_static(member, membername, isattr, parent)

    @classmethod
    def can_document_member_static(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        raise NotImplementedError


# Define __all__ for this module
__all__ = ['DocstringSignatureMixin', 'ClassLevelDocumenter']
