from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING

from sphinx.errors import PycodeError
from sphinx.events import EventManager
from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
from sphinx.ext.autodoc._property_types import _ClassDefProperties, _ModuleProperties
from sphinx.ext.autodoc._sentinels import ALL, INSTANCE_ATTR, SLOTS_ATTR
from sphinx.ext.autodoc.mock import ismock, undecorate
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.docstrings import separate_metadata
from sphinx.util.inspect import (
    getannotations,
    getdoc,
    getmro,
    getslots,
    isclass,
    isenumclass,
    safe_getattr,
    unwrap_all,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Set
    from typing import Any

    from sphinx.events import EventManager
    from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
    from sphinx.ext.autodoc._property_types import (
        _ClassDefProperties,
        _ModuleProperties,
    )
    from sphinx.ext.autodoc.importer import _AttrGetter

logger = logging.getLogger('sphinx.ext.autodoc')
special_member_re = re.compile(r'^__\S+__$')


class ObjectMember:
    """A member of object.

    This is used for the result of `Documenter.get_module_members()` to
    represent each member of the object.
    """

    __slots__ = '__name__', 'object', 'docstring', 'class_', 'skipped'

    __name__: str
    object: Any
    docstring: str | None
    class_: Any
    skipped: bool

    def __init__(
        self,
        name: str,
        obj: Any,
        *,
        docstring: str | None = None,
        class_: Any = None,
        skipped: bool = False,
    ) -> None:
        self.__name__ = name
        self.object = obj
        self.docstring = docstring
        self.class_ = class_
        self.skipped = skipped

    def __repr__(self) -> str:
        return (
            f'ObjectMember('
            f'name={self.__name__!r}, '
            f'obj={self.object!r}, '
            f'docstring={self.docstring!r}, '
            f'class_={self.class_!r}, '
            f'skipped={self.skipped!r}'
            f')'
        )


def _get_members_to_document(
    *,
    want_all: bool,
    analyzer: ModuleAnalyzer | None,
    events: EventManager,
    get_attr: _AttrGetter,
    inherit_docstrings: bool,
    options: _AutoDocumenterOptions,
    orig_name: str,
    props: _ModuleProperties | _ClassDefProperties,
) -> list[tuple[str, Any, bool]]:
    """Find out which members are documentable

    If *want_all* is True, return all members.  Else, only return those
    members given by *self.options.members* (which may also be None).

    Filter the given member list.

    Members are skipped if

    - they are private (except if given explicitly or the private-members
      option is set)
    - they are special methods (except if given explicitly or the
      special-members option is set)
    - they are undocumented (except if the undoc-members option is set)

    The user can override the skipping decision by connecting to the
    ``autodoc-skip-member`` event.
    """
    if props.obj_type == 'module':
        attr_docs = analyzer.attr_docs if analyzer else {}
        members_: dict[str, ObjectMember] = {}
        for name in dir(props._obj):
            try:
                value = safe_getattr(props._obj, name, None)
                if ismock(value):
                    value = undecorate(value)
                docstring = attr_docs.get(('', name), [])
                members_[name] = ObjectMember(
                    name, value, docstring='\n'.join(docstring)
                )
            except AttributeError:
                continue

        # annotation only member (ex. attr: int)
        for name in inspect.getannotations(props._obj):
            if name not in members_:
                docstring = attr_docs.get(('', name), [])
                members_[name] = ObjectMember(
                    name, INSTANCE_ATTR, docstring='\n'.join(docstring)
                )

        if want_all:
            members = list(members_.values())

            module_all = props.all
            if options.ignore_module_all or module_all is None:
                pass
            else:
                module_all_set = frozenset(module_all)
                for member in members:
                    if member.__name__ not in module_all_set:
                        member.skipped = True
        else:
            assert options.members is not ALL
            members = [
                members_[name] for name in options.members or () if name in members_
            ]
            for name in options.members or ():
                if name in members_:
                    continue
                logger.warning(
                    __(
                        'missing attribute mentioned in :members: option: '
                        'module %s, attribute %s'
                    ),
                    safe_getattr(props._obj, '__name__', '???'),
                    name,
                    type='autodoc',
                )
    elif props.obj_type in {'class', 'exception'}:
        members_ = get_class_members(
            props._obj,
            props.parts,
            get_attr,
            inherit_docstrings,
        )
        if want_all:
            members = list(members_.values())
            if not options.inherited_members:
                members = [m for m in members if m.class_ == props._obj]
        else:
            # specific members given
            assert options.members is not ALL
            members = [
                members_[name] for name in options.members or () if name in members_
            ]
            for name in options.members or ():
                if name in members_:
                    continue
                msg = __('missing attribute %s in object %s')
                logger.warning(msg, name, props.full_name, type='autodoc')
    else:
        raise ValueError

    inherited_members: Set[str] = frozenset(options.inherited_members or ())

    filtered = []

    # search for members in source code too
    namespace = props.dotted_parts  # will be empty for modules

    if analyzer:
        attr_docs = analyzer.find_attr_docs()
    else:
        attr_docs = {}

    # process members and determine which to skip
    for obj in members:
        member_name = obj.__name__
        member = obj.object
        has_attr_doc = (namespace, member_name) in attr_docs
        try:
            keep = _should_keep_member(
                member_name,
                member,
                member_obj=obj,
                get_attr=get_attr,
                has_attr_doc=has_attr_doc,
                inherit_docstrings=inherit_docstrings,
                inherited_members=inherited_members,
                options=options,
                parent=props._obj,
                want_all=want_all,
            )
        except Exception as exc:
            logger.warning(
                __(
                    'autodoc: failed to determine %s.%s (%r) to be documented, '
                    'the following exception was raised:\n%s'
                ),
                orig_name,
                member_name,
                member,
                exc,
                type='autodoc',
            )
            keep = False

        # give the user a chance to decide whether this member
        # should be skipped
        if events is not None:
            # let extensions preprocess docstrings
            skip_user = events.emit_firstresult(
                'autodoc-skip-member',
                props.obj_type,
                member_name,
                member,
                not keep,
                options,
            )
            if skip_user is not None:
                keep = not skip_user

        if keep:
            # if is_attr is True, the member is documented as an attribute
            is_attr = member is INSTANCE_ATTR or has_attr_doc
            filtered.append((member_name, member, is_attr))

    return filtered


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


def _should_keep_member(
    member_name: str,
    member: Any,
    member_obj: ObjectMember | Any,
    *,
    get_attr: _AttrGetter,
    has_attr_doc: bool,
    inherit_docstrings: bool,
    inherited_members: Set[str],
    options: _AutoDocumenterOptions,
    parent: Any,
    want_all: bool,
) -> bool:
    exclude_members = options.exclude_members
    special_members = options.special_members
    private_members = options.private_members
    undoc_members = options.undoc_members

    doc = getdoc(
        member,
        get_attr,
        inherit_docstrings,
        parent,
        member_name,
    )
    if not isinstance(doc, str):
        # Ignore non-string __doc__
        doc = None

    # if the member __doc__ is the same as self's __doc__, it's just
    # inherited and therefore not the member's doc
    cls = get_attr(member, '__class__', None)
    if cls:
        cls_doc = get_attr(cls, '__doc__', None)
        if cls_doc == doc:
            doc = None

    if isinstance(member_obj, ObjectMember) and member_obj.docstring:
        # hack for ClassDocumenter to inject docstring via ObjectMember
        doc = member_obj.docstring

    doc, metadata = separate_metadata(doc)
    has_doc = bool(doc)

    if 'private' in metadata:
        # consider a member private if docstring has "private" metadata
        is_private = True
    elif 'public' in metadata:
        # consider a member public if docstring has "public" metadata
        is_private = False
    else:
        is_private = member_name.startswith('_')

    keep = False
    if ismock(member) and not has_attr_doc:
        # mocked module or object
        pass
    elif exclude_members and member_name in exclude_members:
        # remove members given by exclude-members
        keep = False
    elif want_all and special_member_re.match(member_name):
        # special __methods__
        if special_members and member_name in special_members:
            if member_name == '__doc__':  # NoQA: SIM114
                keep = False
            elif _is_filtered_inherited_member(
                member_name,
                member_obj,
                parent=parent,
                inherited_members=inherited_members,
                get_attr=get_attr,
            ):
                keep = False
            else:
                keep = bool(has_doc or undoc_members)
        else:
            keep = False
    elif has_attr_doc:
        if want_all and is_private:
            if private_members is None:
                keep = False
            else:
                keep = member_name in private_members
        else:
            # keep documented attributes
            keep = True
    elif want_all and is_private:
        if has_doc or undoc_members:
            if private_members is None:  # NoQA: SIM114
                keep = False
            elif _is_filtered_inherited_member(
                member_name,
                member_obj,
                parent=parent,
                inherited_members=inherited_members,
                get_attr=get_attr,
            ):
                keep = False
            else:
                keep = member_name in private_members
        else:
            keep = False
    else:
        if options.members is ALL and _is_filtered_inherited_member(
            member_name,
            member_obj,
            parent=parent,
            inherited_members=inherited_members,
            get_attr=get_attr,
        ):
            keep = False
        else:
            # ignore undocumented members if :undoc-members: is not given
            keep = has_doc or undoc_members  # type: ignore[assignment]

    if isinstance(member_obj, ObjectMember) and member_obj.skipped:
        # forcedly skipped member (ex. a module attribute not defined in __all__)
        keep = False
    return keep


def _is_filtered_inherited_member(
    member_name: str,
    member_obj: Any,
    *,
    parent: Any,
    inherited_members: Set[str],
    get_attr: _AttrGetter,
) -> bool:
    seen = set()

    if not inspect.isclass(parent):
        return False

    for cls in parent.__mro__:
        if member_name in cls.__dict__:
            seen.add(cls)
        if (
            cls.__name__ in inherited_members
            and cls != parent
            and any(issubclass(potential_child, cls) for potential_child in seen)
        ):
            # given member is a member of specified *super class*
            return True
        if member_name in cls.__dict__:
            return False
        if member_name in get_attr(cls, '__annotations__', {}):
            return False
        if isinstance(member_obj, ObjectMember) and member_obj.class_ is cls:
            return False
    return False
