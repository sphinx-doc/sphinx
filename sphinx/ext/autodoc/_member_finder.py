from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._sentinels import INSTANCE_ATTR, SLOTS_ATTR
from sphinx.ext.autodoc.mock import ismock, undecorate
from sphinx.pycode import ModuleAnalyzer
from sphinx.util.inspect import (
    getannotations,
    getmro,
    getslots,
    isclass,
    isenumclass,
    safe_getattr,
    unwrap_all,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from typing import Any, Protocol

    from sphinx.ext.autodoc import ObjectMember

    class _AttrGetter(Protocol):
        def __call__(self, obj: Any, name: str, default: Any = ..., /) -> Any: ...


def _filter_enum_dict(
    enum_class: type[Enum],
    attrgetter: _AttrGetter,
    enum_class_dict: Mapping[str, object],
) -> Iterator[tuple[str, type, Any]]:
    """Find the attributes to document of an enumeration class.

    The output consists of triplets ``(attribute name, defining class, value)``
    where the attribute name can appear more than once during the iteration
    but with different defining class. The order of occurrence is guided by
    the MRO of *enum_class*.
    """
    # attributes that were found on a mixin type or the data type
    candidate_in_mro: set[str] = set()
    # sunder names that were picked up (and thereby allowed to be redefined)
    # see: https://docs.python.org/3/howto/enum.html#supported-dunder-names
    sunder_names = {
        '_name_',
        '_value_',
        '_missing_',
        '_order_',
        '_generate_next_value_',
    }
    # attributes that can be picked up on a mixin type or the enum's data type
    public_names = {'name', 'value', *object.__dict__, *sunder_names}
    # names that are ignored by default
    ignore_names = Enum.__dict__.keys() - public_names

    def should_ignore(name: str, value: Any) -> bool:
        if name in sunder_names:
            return _is_native_enum_api(value, name)
        return name in ignore_names

    sentinel = object()

    def query(name: str, defining_class: type) -> tuple[str, type, Any] | None:
        value = attrgetter(enum_class, name, sentinel)
        if value is not sentinel:
            return name, defining_class, value
        return None

    # attributes defined on a parent type, possibly shadowed later by
    # the attributes defined directly inside the enumeration class
    for parent in enum_class.__mro__:
        if parent in {enum_class, Enum, object}:
            continue

        parent_dict = attrgetter(parent, '__dict__', {})
        for name, value in parent_dict.items():
            if should_ignore(name, value):
                continue

            candidate_in_mro.add(name)
            if (item := query(name, parent)) is not None:
                yield item

    # exclude members coming from the native Enum unless
    # they were redefined on a mixin type or the data type
    excluded_members = Enum.__dict__.keys() - candidate_in_mro
    yield from filter(
        None,
        (
            query(name, enum_class)
            for name in enum_class_dict
            if name not in excluded_members
        ),
    )

    # check if allowed members from ``Enum`` were redefined at the enum level
    special_names = sunder_names | public_names
    special_names &= enum_class_dict.keys()
    special_names &= Enum.__dict__.keys()
    for name in special_names:
        if (
            not _is_native_enum_api(enum_class_dict[name], name)
            and (item := query(name, enum_class)) is not None
        ):
            yield item


def _is_native_enum_api(obj: object, name: str) -> bool:
    """Check whether *obj* is the same as ``Enum.__dict__[name]``."""
    return unwrap_all(obj) is unwrap_all(Enum.__dict__[name])


def unmangle(subject: Any, name: str) -> str | None:
    """Unmangle the given name."""
    try:
        if isclass(subject) and not name.endswith('__'):
            prefix = f'_{subject.__name__}__'
            if name.startswith(prefix):
                return name.replace(prefix, '__', 1)
            else:
                for cls in subject.__mro__:
                    prefix = f'_{cls.__name__}__'
                    if name.startswith(prefix):
                        # mangled attribute defined in parent class
                        return None
    except AttributeError:
        pass

    return name


def get_class_members(
    subject: Any, objpath: Any, attrgetter: _AttrGetter, inherit_docstrings: bool = True
) -> dict[str, ObjectMember]:
    """Get members and attributes of target class."""
    from sphinx.ext.autodoc._documenters import ObjectMember

    # the members directly defined in the class
    obj_dict = attrgetter(subject, '__dict__', {})

    members: dict[str, ObjectMember] = {}

    # enum members
    if isenumclass(subject):
        for name, defining_class, value in _filter_enum_dict(
            subject, attrgetter, obj_dict
        ):
            # the order of occurrence of *name* matches the subject's MRO,
            # allowing inherited attributes to be shadowed correctly
            if unmangled := unmangle(defining_class, name):
                members[unmangled] = ObjectMember(
                    unmangled, value, class_=defining_class
                )

    # members in __slots__
    try:
        subject___slots__ = getslots(subject)
        if subject___slots__:
            for name, docstring in subject___slots__.items():
                members[name] = ObjectMember(
                    name, SLOTS_ATTR, class_=subject, docstring=docstring
                )
    except (TypeError, ValueError):
        pass

    # other members
    for name in dir(subject):
        try:
            value = attrgetter(subject, name)
            if ismock(value):
                value = undecorate(value)

            unmangled = unmangle(subject, name)
            if unmangled and unmangled not in members:
                if name in obj_dict:
                    members[unmangled] = ObjectMember(unmangled, value, class_=subject)
                else:
                    members[unmangled] = ObjectMember(unmangled, value)
        except AttributeError:
            continue

    try:
        for cls in getmro(subject):
            try:
                modname = safe_getattr(cls, '__module__')
                qualname = safe_getattr(cls, '__qualname__')
                analyzer = ModuleAnalyzer.for_module(modname)
                analyzer.analyze()
            except AttributeError:
                qualname = None
                analyzer = None
            except PycodeError:
                analyzer = None

            # annotation only member (ex. attr: int)
            for name in getannotations(cls):
                unmangled = unmangle(cls, name)
                if unmangled and unmangled not in members:
                    if analyzer and (qualname, unmangled) in analyzer.attr_docs:
                        docstring = '\n'.join(analyzer.attr_docs[qualname, unmangled])
                    else:
                        docstring = None

                    members[unmangled] = ObjectMember(
                        unmangled, INSTANCE_ATTR, class_=cls, docstring=docstring
                    )

            # append or complete instance attributes (cf. self.attr1) if analyzer knows
            if analyzer:
                for (ns, name), docstring in analyzer.attr_docs.items():
                    if ns == qualname and name not in members:
                        # otherwise unknown instance attribute
                        members[name] = ObjectMember(
                            name,
                            INSTANCE_ATTR,
                            class_=cls,
                            docstring='\n'.join(docstring),
                        )
                    elif (
                        ns == qualname
                        and docstring
                        and isinstance(members[name], ObjectMember)
                        and not members[name].docstring
                    ):
                        if cls != subject and not inherit_docstrings:
                            # If we are in the MRO of the class and not the class itself,
                            # and we do not want to inherit docstrings, then skip setting
                            # the docstring below
                            continue
                        # attribute is already known, because dir(subject) enumerates it.
                        # But it has no docstring yet
                        members[name].docstring = '\n'.join(docstring)
    except AttributeError:
        pass

    return members
