from __future__ import annotations

from typing import TYPE_CHECKING, NewType, TypeVar

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._sentinels import (
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.importer import (
    _import_from_module_and_path,
    _ImportedObject,
    import_module,
)
from sphinx.ext.autodoc.mock import ismock, mock, undecorate
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import safe_getattr
from sphinx.util.typing import get_type_hints

if TYPE_CHECKING:
    from collections.abc import Sequence
    from typing import Any

    from sphinx.ext.autodoc.importer import _AttrGetter

logger = logging.getLogger('sphinx.ext.autodoc')


def _import_object(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject:
    """Import the object given by *module_name* and *obj_path* and set
    it as *object*.

    Returns True if successful, False if an error occurred.
    """
    try:
        with mock(mock_imports):
            im = _import_from_module_and_path(
                module_name=module_name, obj_path=obj_path, get_attr=get_attr
            )
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
        return im
    except ImportError:  # NoQA: TRY203
        raise


def _import_class(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject:
    try:
        with mock(mock_imports):
            im = _import_from_module_and_path(
                module_name=module_name, obj_path=obj_path, get_attr=get_attr
            )
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError:  # NoQA: TRY203
        raise

    # if the class is documented under another name, document it
    # as data/attribute
    if hasattr(im.obj, '__name__'):
        im.doc_as_attr = obj_path[-1] != im.obj.__name__
    else:
        im.doc_as_attr = True

    if isinstance(im.obj, NewType | TypeVar):
        obj_module_name = getattr(im.obj, '__module__', module_name)
        if obj_module_name != module_name and module_name.startswith(obj_module_name):
            bases = module_name[len(obj_module_name) :].strip('.').split('.')
            im.objpath = bases + list(obj_path)
            im.modname = obj_module_name
    return im


def _import_method(
    *,
    module_name: str,
    obj_path: Sequence[str],
    member_order: int,
    mock_imports: list[str],
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject:
    try:
        with mock(mock_imports):
            im = _import_from_module_and_path(
                module_name=module_name, obj_path=obj_path, get_attr=get_attr
            )
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError:  # NoQA: TRY203
        raise

    # to distinguish classmethod/staticmethod
    obj = im.parent.__dict__.get(im.object_name, im.obj)
    if inspect.isstaticmethod(obj, cls=im.parent, name=im.object_name):
        # document static members before regular methods
        im.member_order = member_order - 1
    elif inspect.isclassmethod(obj):
        # document class methods before static methods as
        # they usually behave as alternative constructors
        im.member_order = member_order - 2
    return im


def _import_property(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject | None:
    try:
        with mock(mock_imports):
            im = _import_from_module_and_path(
                module_name=module_name, obj_path=obj_path, get_attr=get_attr
            )
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError:  # NoQA: TRY203
        raise

    if not inspect.isproperty(im.obj):
        # Support for class properties. Note: these only work on Python 3.9.
        __dict__ = safe_getattr(im.parent, '__dict__', {})
        obj = __dict__.get(obj_path[-1])
        if isinstance(obj, classmethod) and inspect.isproperty(obj.__func__):
            im.obj = obj.__func__
            im.isclassmethod = True
            return im
        else:
            return None

    return im


def _import_assignment_data(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    type_aliases: dict[str, Any] | None,
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject:
    import_failed = True
    try:
        with mock(mock_imports):
            im = _import_from_module_and_path(
                module_name=module_name, obj_path=obj_path, get_attr=get_attr
            )
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
        import_failed = False
    except ImportError as exc:
        # annotation only instance variable (PEP-526)
        try:
            with mock(mock_imports):
                parent = import_module(module_name)
            annotations = get_type_hints(
                parent, None, type_aliases, include_extras=True
            )
            if obj_path[-1] in annotations:
                im = _ImportedObject(
                    parent=parent,
                    obj=UNINITIALIZED_ATTR,
                )
                import_failed = False
        except ImportError:
            pass

        if import_failed:
            raise

    # Update __annotations__ to support type_comment and so on
    annotations = dict(inspect.getannotations(im.parent))
    im.parent.__annotations__ = annotations

    try:
        analyzer = ModuleAnalyzer.for_module(module_name)
        analyzer.analyze()
        for (classname, attrname), annotation in analyzer.annotations.items():
            if not classname and attrname not in annotations:
                annotations[attrname] = annotation
    except PycodeError:
        pass
    return im


def _import_assignment_attribute(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    type_aliases: dict[str, Any] | None,
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject:
    import_failed = True
    try:
        with mock(mock_imports):
            im = _import_from_module_and_path(
                module_name=module_name, obj_path=obj_path, get_attr=get_attr
            )
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
        import_failed = False
    except ImportError as exc:
        # Support runtime & uninitialized instance attributes.
        #
        # The former are defined in __init__() methods with doc-comments.
        # The latter are PEP-526 style annotation only annotations.
        #
        # class Foo:
        #     attr: int  #: uninitialized attribute
        #
        #     def __init__(self):
        #         self.attr = None  #: runtime attribute
        try:
            with mock(mock_imports):
                ret = _import_from_module_and_path(
                    module_name=module_name, obj_path=obj_path[:-1], get_attr=get_attr
                )
            parent = ret.obj
            if _is_runtime_instance_attribute(parent=parent, obj_path=obj_path):
                im = _ImportedObject(
                    parent=parent,
                    obj=RUNTIME_INSTANCE_ATTRIBUTE,
                )
                import_failed = False
            elif _is_uninitialized_instance_attribute(
                parent=parent, obj_path=obj_path, type_aliases=type_aliases
            ):
                im = _ImportedObject(
                    parent=parent,
                    obj=UNINITIALIZED_ATTR,
                )
                import_failed = False
        except ImportError:
            pass

        if import_failed:
            raise

    if _is_slots_attribute(parent=im.parent, obj_path=obj_path):
        im.obj = SLOTS_ATTR
    elif inspect.isenumattribute(im.obj):
        im.obj = im.obj.value
    if im.parent:
        # Update __annotations__ to support type_comment and so on.
        try:
            annotations = dict(inspect.getannotations(im.parent))
            im.parent.__annotations__ = annotations

            for cls in inspect.getmro(im.parent):
                try:
                    module = safe_getattr(cls, '__module__')
                    qualname = safe_getattr(cls, '__qualname__')

                    analyzer = ModuleAnalyzer.for_module(module)
                    analyzer.analyze()
                    anns = analyzer.annotations
                    for (classname, attrname), annotation in anns.items():
                        if classname == qualname and attrname not in annotations:
                            annotations[attrname] = annotation
                except (AttributeError, PycodeError):
                    pass
        except (AttributeError, TypeError):
            # Failed to set __annotations__ (built-in, extensions, etc.)
            pass

    if im and not inspect.isattributedescriptor(im.obj):
        im._non_data_descriptor = True
    else:
        im._non_data_descriptor = False

    return im


def _is_runtime_instance_attribute(*, parent: Any, obj_path: Sequence[str]) -> bool:
    """Check the subject is an attribute defined in __init__()."""
    # An instance variable defined in __init__().
    if _get_attribute_comment(parent=parent, obj_path=obj_path, attrname=obj_path[-1]):
        return True
    return _is_runtime_instance_attribute_not_commented(
        parent=parent, obj_path=obj_path
    )


def _is_runtime_instance_attribute_not_commented(
    *, parent: Any, obj_path: Sequence[str]
) -> bool:
    """Check the subject is an attribute defined in __init__() without comment."""
    for cls in inspect.getmro(parent):
        try:
            module = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')

            analyzer = ModuleAnalyzer.for_module(module)
            analyzer.analyze()
            if qualname and obj_path:
                key = f'{qualname}.{obj_path[-1]}'
                if key in analyzer.tagorder:
                    return True
        except (AttributeError, PycodeError):
            pass

    return False


def _get_attribute_comment(
    parent: Any, obj_path: Sequence[str], attrname: str
) -> list[str] | None:
    for cls in inspect.getmro(parent):
        try:
            module = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')

            analyzer = ModuleAnalyzer.for_module(module)
            analyzer.analyze()
            if qualname and obj_path:
                key = (qualname, attrname)
                if key in analyzer.attr_docs:
                    return list(analyzer.attr_docs[key])
        except (AttributeError, PycodeError):
            pass

    return None


def _is_uninitialized_instance_attribute(
    *, parent: Any, obj_path: Sequence[str], type_aliases: dict[str, Any] | None
) -> bool:
    """Check the subject is an annotation only attribute."""
    annotations = get_type_hints(parent, None, type_aliases, include_extras=True)
    return obj_path[-1] in annotations


def _is_slots_attribute(*, parent: Any, obj_path: Sequence[str]) -> bool:
    """Check the subject is an attribute in __slots__."""
    try:
        if parent___slots__ := inspect.getslots(parent):
            return obj_path[-1] in parent___slots__
        else:
            return False
    except (ValueError, TypeError):
        return False
