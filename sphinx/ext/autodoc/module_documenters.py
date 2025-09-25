from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, Sequence

from sphinx.ext.autodoc.documenter_base import Documenter
from sphinx.util.typing import OptionSpec

if TYPE_CHECKING:
    from sphinx.ext.autodoc._property_types import _ModuleProperties


class ModuleDocumenter(Documenter):
    """Specialized Documenter subclass for modules."""

    props: _ModuleProperties

    objtype = 'module'
    content_indent = ''
    _extra_indent = '   '

    option_spec: ClassVar[OptionSpec] = {
        'members': True,
        'undoc-members': False,
        'no-index': False,
        'no-index-entry': False,
        'inherited-members': False,
        'show-inheritance': False,
        'synopsis': '',
        'platform': '',
        'deprecated': False,
        'member-order': 'alphabetical',
        'exclude-members': [],
        'private-members': None,
        'special-members': None,
        'imported-members': False,
        'ignore-module-all': False,
        'no-value': False,
        'noindex': False,
    }

    def __init__(self, *args: Any) -> None:
        super().__init__(*args)
        self.options = self.options.merge_member_options()
        self.__all__: Sequence[str] | None = None

    def add_content(self, more_content: Any) -> None:
        old_indent = self.indent
        self.indent += self._extra_indent
        super().add_content(None)
        self.indent = old_indent
        if more_content:
            for line, src in zip(more_content.data, more_content.items, strict=True):
                self.add_line(line, src[0], src[1])

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        # don't document submodules automatically
        return False

    def _module_all(self) -> Sequence[str] | None:
        if self.__all__ is None and not self.options.ignore_module_all:
            self.__all__ = self.props.all
        return self.__all__

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)

        sourcename = self.get_sourcename()

        # add some module-specific options
        if self.options.synopsis:
            self.add_line('   :synopsis: ' + self.options.synopsis, sourcename)
        if self.options.platform:
            self.add_line('   :platform: ' + self.options.platform, sourcename)
        if self.options.deprecated:
            self.add_line('   :deprecated:', sourcename)

    def sort_members(
        self, documenters: list[tuple[Documenter, bool]], order: str
    ) -> list[tuple[Documenter, bool]]:
        module_all = self.props.all
        if (
            order == 'bysource'
            and not self.options.ignore_module_all
            and module_all is not None
        ):
            assert module_all is not None
            module_all_set = frozenset(module_all)
            module_all_len = len(module_all)

            # Sort alphabetically first (for members not listed on the __all__)
            documenters.sort(key=lambda e: e[0].name)

            # Move members listed in __all__ to the front
            documenters_with_all = []
            documenters_without_all = []
            for documenter, _ in documenters:
                if documenter.name in module_all_set:
                    documenters_with_all.append((documenter, False))
                else:
                    documenters_without_all.append((documenter, False))

            return documenters_with_all + documenters_without_all
        else:
            return super().sort_members(documenters, order)

    def document_members(self, want_all: bool = True, **kwargs: Any) -> None:
        """Generate reST for the members of the module."""
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


class ModuleLevelDocumenter(Documenter):
    """Base class for documenters that document module-level objects."""

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
__all__ = ['ModuleDocumenter', 'ModuleLevelDocumenter']
