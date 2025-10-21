from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from sphinx.ext.autodoc import ClassDocumenter, bool_option
from sphinx.ext.autodoc._generate import _docstring_source_name

if TYPE_CHECKING:
    from typing import Any

    from docutils.statemachine import StringList

    from sphinx.application import Sphinx
    from sphinx.ext.autodoc import Documenter
    from sphinx.util.typing import ExtensionMetadata


class IntEnumDocumenter(ClassDocumenter):
    objtype = 'intenum'
    directivetype = ClassDocumenter.objtype
    priority = 25
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

    def add_line(self, line: str, source: str = '', *lineno: int, indent: str) -> None:
        """Append one line of generated reST to the output."""
        analyzer_source = '' if self.analyzer is None else self.analyzer.srcname
        source_name = _docstring_source_name(props=self.props, source=analyzer_source)
        if line.strip():  # not a blank line
            self.result.append(indent + line, source_name, *lineno)
        else:
            self.result.append('', source_name, *lineno)

    def add_directive_header(self, *, indent: str) -> None:
        super().add_directive_header(indent=indent)
        self.add_line('   :final:', indent=indent)

    def add_content(self, more_content: StringList | None, *, indent: str) -> None:
        super().add_content(more_content, indent=indent)

        enum_object: IntEnum = self.props._obj
        use_hex = self.options.hex
        self.add_line('', indent=indent)

        for the_member_name, enum_member in enum_object.__members__.items():  # type: ignore[attr-defined]
            the_member_value = enum_member.value
            if use_hex:
                the_member_value = hex(the_member_value)

            self.add_line(f'**{the_member_name}**: {the_member_value}', indent=indent)
            self.add_line('', indent=indent)


def setup(app: Sphinx) -> ExtensionMetadata:
    app.setup_extension('sphinx.ext.autodoc')  # Require autodoc extension
    app.add_autodocumenter(IntEnumDocumenter)
    return {
        'version': '1',
        'parallel_read_safe': True,
    }
