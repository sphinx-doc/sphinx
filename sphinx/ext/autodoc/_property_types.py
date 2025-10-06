from __future__ import annotations

import dataclasses

from sphinx.ext.autodoc._sentinels import RUNTIME_INSTANCE_ATTRIBUTE, UNINITIALIZED_ATTR

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path
    from typing import Any, Literal, TypeAlias

    from sphinx.ext.autodoc._sentinels import (
        RUNTIME_INSTANCE_ATTRIBUTE_T,
        SLOTS_ATTR_T,
        UNINITIALIZED_ATTR_T,
    )

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
    _obj___qualname__: str | None
    _obj_bases: tuple[str, ...]
    _obj_is_new_type: bool
    _obj_is_typevar: bool

    @property
    def doc_as_attr(self) -> bool:
        # if the class is documented under another name, document it
        # as data/attribute
        if self._obj___name__ is None:
            return True
        return self.parts[-1] != self._obj___name__

    @property
    def canonical_full_name(self) -> str | None:
        modname = self._obj___module__
        if modname is None:
            modname = self.module_name
        qualname = self._obj___qualname__
        if qualname is None:
            qualname = self._obj___name__
        if not modname or not qualname or '<locals>' in qualname:
            # No valid qualname found if the object is defined as locals
            return None
        return f'{modname}.{qualname}'


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _FunctionDefProperties(_ItemProperties):
    obj_type: Literal['function', 'method', 'property', 'decorator']

    properties: frozenset[_AutodocFuncProperty]

    _obj___name__: str | None
    _obj___qualname__: str | None
    _obj_property_type_annotation: str | None = 'default'

    @property
    def is_abstractmethod(self) -> bool:
        return 'abstractmethod' in self.properties

    @property
    def is_async(self) -> bool:
        return 'async' in self.properties

    @property
    def is_classmethod(self) -> bool:
        return 'classmethod' in self.properties

    @property
    def is_final(self) -> bool:
        return 'final' in self.properties

    # @property
    # def is_singledispatch(self) -> bool:
    #     return 'singledispatch' in self.properties

    @property
    def is_staticmethod(self) -> bool:
        return 'staticmethod' in self.properties


@dataclasses.dataclass(frozen=False, kw_only=True, slots=True)
class _AssignStatementProperties(_ItemProperties):
    obj_type: Literal['attribute', 'data']

    value: object
    annotation: str

    class_var: bool
    instance_var: bool

    _obj_is_generic_alias: bool
    _obj_is_attribute_descriptor: bool
    _obj_is_mock: bool
    _obj_is_sentinel: (
        RUNTIME_INSTANCE_ATTRIBUTE_T | SLOTS_ATTR_T | UNINITIALIZED_ATTR_T | None
    )
    _obj_repr_rst: str
    _obj_type_annotation: str | None
