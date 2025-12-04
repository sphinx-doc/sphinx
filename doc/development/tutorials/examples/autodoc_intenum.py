from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from sphinx.ext.autodoc import ClassDocumenter, Documenter, bool_option

if TYPE_CHECKING:
    from typing import Any

    from docutils.statemachine import StringList

    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class IntEnumDocumenter(ClassDocumenter):
    objtype = 'intenum'
    directivetype = ClassDocumenter.objtype
    priority = 10 + ClassDocumenter.priority
    option_spec = dict(ClassDocumenter.option_spec)
    option_spec['hex'] = bool_option

    @classmethod
    def can_document_member(
        cls, member: Any, membername: str, isattr: bool, parent: Documenter
    ) -> bool:
        try:
            return issubclass(member, IntEnum)
        except TypeError:
            return False

    def add_directive_header(self, sig: str) -> None:
        super().add_directive_header(sig)
        self.add_line('   :final:', self.get_sourcename())

    def add_content(
        self,
        more_content: StringList | None,
    ) -> None:
        super().add_content(more_content)

        source_name = self.get_sourcename()
        enum_object: IntEnum = self.object
        use_hex = self.options.hex
        self.add_line('', source_name)

        for the_member_name, enum_member in enum_object.__members__.items():  # type: ignore[attr-defined]
            the_member_value = enum_member.value
            if use_hex:
                the_member_value = hex(the_member_value)

            self.add_line(f'**{the_member_name}**: {the_member_value}', source_name)
            self.add_line('', source_name)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.setup_extension('sphinx.ext.autodoc')  # Require autodoc extension
    app.add_autodocumenter(IntEnumDocumenter)
    return {
        'version': '1',
        'parallel_read_safe': True,
    }
