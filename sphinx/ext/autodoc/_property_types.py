from __future__ import annotations

import dataclasses

from sphinx.ext.autodoc._sentinels import RUNTIME_INSTANCE_ATTRIBUTE, UNINITIALIZED_ATTR

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Any, Literal, TypeAlias

    _AutodocObjType: TypeAlias = Literal[
        'module',
        'class',
        'exception',
        'function',
        'decorator',
        'method',
        'property',
        'attribute',
        'data',
    ]
    _AutodocFuncProperty: TypeAlias = Literal[
        'abstractmethod',
        'async',
        'classmethod',
        'final',
        'singledispatch',
        'staticmethod',
    ]


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _ItemProperties:
    #: The kind of object being documented
    obj_type: _AutodocObjType
    #: The dotted module name
    module_name: str
    #: The fully-qualified name within the module
    parts: tuple[str, ...]
    #: This item's docstring, as a sequence of lines
    docstring_lines: tuple[str, ...]

    _obj: Any
    _obj___module__: str | None

    @property
    def name(self) -> str:
        """The name of the item"""
        return self.parts[-1]

    @property
    def object_name(self) -> str:
        if self._obj is RUNTIME_INSTANCE_ATTRIBUTE or self._obj is UNINITIALIZED_ATTR:
            return ''
        return self.name

    @property
    def full_name(self) -> str:
        return '.'.join((self.module_name, *self.parts))

    @property
    def parent_names(self) -> tuple[str, ...]:
        return self.parts[:-1]

    @property
    def dotted_parts(self) -> str:
        return '.'.join(self.parts)


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _ModuleProperties(_ItemProperties):
    obj_type: Literal['module'] = 'module'
    parts: tuple[()] = ()  # modules have no parts

    file_path: Path | None
    all: Sequence[str] | None

    @property
    def name(self) -> str:
        return self.module_name.rpartition('.')[2]

    @property
    def object_name(self) -> str:
        return ''

    @property
    def full_name(self) -> str:
        return self.module_name

    @property
    def parent_names(self) -> tuple[str, ...]:
        return tuple(self.module_name.split('.')[:-1])


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _ClassDefProperties(_ItemProperties):
    obj_type: Literal['class', 'exception']

    bases: Sequence[tuple[str, ...]] | None

    _obj___name__: str | None

    @property
    def doc_as_attr(self) -> bool:
        # if the class is documented under another name, document it
        # as data/attribute
        if self._obj___name__ is None:
            return True
        return self.parts[-1] != self._obj___name__


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _FunctionDefProperties(_ItemProperties):
    obj_type: Literal['function', 'method', 'property', 'decorator']

    properties: frozenset[_AutodocFuncProperty]

    @property
    def is_classmethod(self) -> bool:
        return 'classmethod' in self.properties


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _AssignStatementProperties(_ItemProperties):
    obj_type: Literal['attribute', 'data']

    value: object
    annotation: str

    class_var: bool
    instance_var: bool
