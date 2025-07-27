from __future__ import annotations

from typing import TYPE_CHECKING, NewType, TypeVar

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._sentinels import (
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.importer import import_module, import_object
from sphinx.ext.autodoc.mock import ismock, mock, undecorate
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import safe_getattr
from sphinx.util.typing import get_type_hints

if TYPE_CHECKING:
    from collections.abc import Sequence
    from types import ModuleType
    from typing import Any

    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment
    from sphinx.ext.autodoc._directive_options import Options
    from sphinx.ext.autodoc.importer import _AttrGetter

logger = logging.getLogger('sphinx.ext.autodoc')


class _Imported:
    module: ModuleType | None

    # the parent/owner of the object to document
    parent: Any

    object_name: str

    # the object to document
    obj: Any

    __all__: Sequence[str] | None
    doc_as_attr: bool
    objpath: list[str]
    modname: str
    member_order: int
    _non_data_descriptor: bool
    isclassmethod: bool

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.__dict__}>'


def _import_object(
    *,
    modname: str,
    objpath: list[str],
    objtype: str,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    raise_error: bool = False,
) -> _Imported | None:
    """Import the object given by *modname* and *objpath* and set
    it as *object*.

    Returns True if successful, False if an error occurred.
    """
    im = _Imported()
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
        return im
    except ImportError as exc:
        if raise_error:
            raise
        logger.warning(exc.args[0], type='autodoc', subtype='import_object')
        env.note_reread()
        return None


def _import_module(
    *,
    modname: str,
    objpath: list[str],
    objtype: str,
    fullname: str,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    options: Options,
    raise_error: bool = False,
) -> _Imported | None:
    im = _Imported()
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError as exc:
        if raise_error:
            raise
        logger.warning(exc.args[0], type='autodoc', subtype='import_object')
        env.note_reread()
        return None

    try:
        if not options.ignore_module_all:
            im.__all__ = inspect.getall(im.obj)
    except ValueError as exc:
        # invalid __all__ found.
        logger.warning(
            __(
                '__all__ should be a list of strings, not %r '
                '(in module %s) -- ignoring __all__'
            ),
            exc.args[0],
            fullname,
            type='autodoc',
        )
    return im


def _import_class(
    *,
    modname: str,
    objpath: list[str],
    objtype: str,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    raise_error: bool = False,
) -> _Imported | None:
    im = _Imported()
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError as exc:
        if raise_error:
            raise
        logger.warning(exc.args[0], type='autodoc', subtype='import_object')
        env.note_reread()
        return None

    # if the class is documented under another name, document it
    # as data/attribute
    if hasattr(im.obj, '__name__'):
        im.doc_as_attr = objpath[-1] != im.obj.__name__
    else:
        im.doc_as_attr = True
    if isinstance(im.obj, NewType | TypeVar):
        obj_modname = getattr(im.obj, '__module__', modname)
        if obj_modname != modname and modname.startswith(obj_modname):
            bases = modname[len(obj_modname) :].strip('.').split('.')
            im.objpath = bases + objpath
            im.modname = obj_modname
    return im


def _import_method(
    *,
    modname: str,
    objpath: list[str],
    objtype: str,
    member_order: int,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    raise_error: bool = False,
) -> _Imported | None:
    im = _Imported()
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError as exc:
        if raise_error:
            raise
        logger.warning(exc.args[0], type='autodoc', subtype='import_object')
        env.note_reread()
        return None

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
    modname: str,
    objpath: list[str],
    objtype: str,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    raise_error: bool = False,
) -> _Imported | None:
    im = _Imported()
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
    except ImportError as exc:
        if raise_error:
            raise
        logger.warning(exc.args[0], type='autodoc', subtype='import_object')
        env.note_reread()
        return None

    if not inspect.isproperty(im.obj):
        __dict__ = safe_getattr(im.parent, '__dict__', {})
        obj = __dict__.get(objpath[-1])
        if isinstance(obj, classmethod) and inspect.isproperty(obj.__func__):
            im.obj = obj.__func__
            im.isclassmethod = True
            return im
        else:
            return None

    im.isclassmethod = False
    return im


def _import_assignment_data(
    *,
    modname: str,
    objpath: list[str],
    objtype: str,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    raise_error: bool = False,
) -> _Imported | None:
    import_failed = True
    im = _Imported()
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
        if ismock(im.obj):
            im.obj = undecorate(im.obj)
        import_failed = False
    except ImportError as exc:
        # annotation only instance variable (PEP-526)
        try:
            with mock(config.autodoc_mock_imports):
                parent = import_module(modname)
            annotations = get_type_hints(
                parent,
                None,
                config.autodoc_type_aliases,
                include_extras=True,
            )
            if objpath[-1] in annotations:
                im.obj = UNINITIALIZED_ATTR
                im.parent = parent
                import_failed = False
        except ImportError:
            pass

        if import_failed:
            if raise_error:
                raise
            logger.warning(exc.args[0], type='autodoc', subtype='import_object')
            env.note_reread()
            return None

    # Update __annotations__ to support type_comment and so on
    annotations = dict(inspect.getannotations(im.parent))
    im.parent.__annotations__ = annotations

    try:
        analyzer = ModuleAnalyzer.for_module(modname)
        analyzer.analyze()
        for (classname, attrname), annotation in analyzer.annotations.items():
            if not classname and attrname not in annotations:
                annotations[attrname] = annotation
    except PycodeError:
        pass
    return im


def _import_assignment_attribute(
    *,
    modname: str,
    objpath: list[str],
    objtype: str,
    get_attr: _AttrGetter,
    config: Config,
    env: BuildEnvironment,
    raise_error: bool = False,
) -> _Imported | None:
    im = _Imported()
    import_failed = True
    try:
        with mock(config.autodoc_mock_imports):
            ret = import_object(modname, objpath, objtype, attrgetter=get_attr)
        im.module, im.parent, im.object_name, im.obj = ret
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
            with mock(config.autodoc_mock_imports):
                ret = import_object(
                    modname,
                    objpath[:-1],
                    'class',
                    attrgetter=get_attr,
                )
            parent = ret[3]
            if _is_runtime_instance_attribute(parent=parent, objpath=objpath):
                im.obj = RUNTIME_INSTANCE_ATTRIBUTE
                im.parent = parent
                import_failed = False
            elif _is_uninitialized_instance_attribute(
                parent=parent, objpath=objpath, config=config
            ):
                im.obj = UNINITIALIZED_ATTR
                im.parent = parent
                import_failed = False
        except ImportError:
            pass

        if import_failed:
            if raise_error:
                raise
            logger.warning(exc.args[0], type='autodoc', subtype='import_object')
            env.note_reread()
            return None

    if _is_slots_attribute(parent=im.parent, objpath=objpath):
        im.obj = SLOTS_ATTR
    elif inspect.isenumattribute(im.obj):
        im.obj = im.obj.value
    if im.parent:
        _update_annotations_attribute_documenter(parent=im.parent)

    if im and not inspect.isattributedescriptor(im.obj):
        im._non_data_descriptor = True
    else:
        im._non_data_descriptor = False

    return im


def _is_runtime_instance_attribute(*, parent: Any, objpath: list[str]) -> bool:
    """Check the subject is an attribute defined in __init__()."""
    # An instance variable defined in __init__().
    if _get_attribute_comment(parent=parent, objpath=objpath, attrname=objpath[-1]):
        return True
    return _is_runtime_instance_attribute_not_commented(parent=parent, objpath=objpath)


def _is_runtime_instance_attribute_not_commented(
    *, parent: Any, objpath: list[str]
) -> bool:
    """Check the subject is an attribute defined in __init__() without comment."""
    for cls in inspect.getmro(parent):
        try:
            module = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')

            analyzer = ModuleAnalyzer.for_module(module)
            analyzer.analyze()
            if qualname and objpath:
                key = f'{qualname}.{objpath[-1]}'
                if key in analyzer.tagorder:
                    return True
        except (AttributeError, PycodeError):
            pass

    return False


def _get_attribute_comment(
    parent: Any, objpath: list[str], attrname: str
) -> list[str] | None:
    for cls in inspect.getmro(parent):
        try:
            module = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')

            analyzer = ModuleAnalyzer.for_module(module)
            analyzer.analyze()
            if qualname and objpath:
                key = (qualname, attrname)
                if key in analyzer.attr_docs:
                    return list(analyzer.attr_docs[key])
        except (AttributeError, PycodeError):
            pass

    return None


def _is_uninitialized_instance_attribute(
    *, parent: Any, objpath: list[str], config: Config
) -> bool:
    """Check the subject is an annotation only attribute."""
    annotations = get_type_hints(
        parent, None, config.autodoc_type_aliases, include_extras=True
    )
    return objpath[-1] in annotations


def _is_slots_attribute(*, parent: Any, objpath: list[str]) -> bool:
    """Check the subject is an attribute in __slots__."""
    try:
        if parent___slots__ := inspect.getslots(parent):
            return objpath[-1] in parent___slots__
        else:
            return False
    except (ValueError, TypeError):
        return False


def _update_annotations_attribute_documenter(*, parent: Any) -> None:
    """Update __annotations__ to support type_comment and so on."""
    try:
        annotations = dict(inspect.getannotations(parent))
        parent.__annotations__ = annotations

        for cls in inspect.getmro(parent):
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
