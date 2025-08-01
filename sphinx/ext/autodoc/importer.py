"""Importer utilities for autodoc"""

from __future__ import annotations

import contextlib
import importlib
import os
import sys
import traceback
import typing
from enum import Enum
from importlib.abc import FileLoader
from importlib.machinery import EXTENSION_SUFFIXES
from importlib.util import decode_source, find_spec, module_from_spec, spec_from_loader
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple, NewType, TypeVar

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._property_types import (
    _AssignStatementProperties,
    _ClassDefProperties,
    _FunctionDefProperties,
    _ItemProperties,
    _ModuleProperties,
)
from sphinx.ext.autodoc._sentinels import (
    INSTANCE_ATTR,
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.mock import ismock, mock, undecorate
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import (
    getannotations,
    getmro,
    getslots,
    isclass,
    isenumclass,
    safe_getattr,
    unwrap_all,
)
from sphinx.util.typing import get_type_hints

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence
    from importlib.machinery import ModuleSpec
    from types import ModuleType
    from typing import Any, Protocol

    from sphinx.environment import BuildEnvironment, _CurrentDocument
    from sphinx.ext.autodoc import ObjectMember
    from sphinx.ext.autodoc._property_types import _AutodocFuncProperty, _AutodocObjType

    class _AttrGetter(Protocol):
        def __call__(self, obj: Any, name: str, default: Any = ..., /) -> Any: ...


_NATIVE_SUFFIXES: frozenset[str] = frozenset({'.pyx', *EXTENSION_SUFFIXES})
logger = logging.getLogger(__name__)


class _ImportedObject:
    #: module containing the object to document
    module: ModuleType | None

    #: parent/owner of the object to document
    parent: Any

    #: name of the object to document
    object_name: str

    #: object to document
    obj: Any

    # ClassDocumenter
    objpath: list[str]
    modname: str

    # MethodDocumenter
    member_order: int

    # PropertyDocumenter
    isclassmethod: bool

    def __init__(
        self,
        *,
        module: ModuleType | None = None,
        parent: Any,
        object_name: str = '',
        obj: Any,
    ) -> None:
        self.module = module
        self.parent = parent
        self.object_name = object_name
        self.obj = obj

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} {self.__dict__}>'


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


def mangle(subject: Any, name: str) -> str:
    """Mangle the given name."""
    try:
        if isclass(subject) and name.startswith('__') and not name.endswith('__'):
            return f'_{subject.__name__}{name}'
    except AttributeError:
        pass

    return name


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


def import_module(modname: str, try_reload: bool = False) -> Any:
    if modname in sys.modules:
        return sys.modules[modname]

    skip_pyi = bool(os.getenv('SPHINX_AUTODOC_IGNORE_NATIVE_MODULE_TYPE_STUBS', ''))
    original_module_names = frozenset(sys.modules)
    try:
        spec = find_spec(modname)
        if spec is None:
            msg = f'No module named {modname!r}'
            raise ModuleNotFoundError(msg, name=modname)  # NoQA: TRY301
        spec, pyi_path = _find_type_stub_spec(spec, modname)
        if skip_pyi or pyi_path is None:
            module = importlib.import_module(modname)
        else:
            if spec.loader is None:
                msg = 'missing loader'
                raise ImportError(msg, name=spec.name)  # NoQA: TRY301
            sys.modules[modname] = module = module_from_spec(spec)
            spec.loader.exec_module(module)
    except ImportError:
        raise
    except BaseException as exc:
        # Importing modules may cause any side effects, including
        # SystemExit, so we need to catch all errors.
        raise ImportError(exc, traceback.format_exc()) from exc
    if try_reload and os.environ.get('SPHINX_AUTODOC_RELOAD_MODULES'):
        new_modules = [m for m in sys.modules if m not in original_module_names]
        # Try reloading modules with ``typing.TYPE_CHECKING == True``.
        try:
            typing.TYPE_CHECKING = True  # type: ignore[misc]
            # Ignore failures; we've already successfully loaded these modules
            with contextlib.suppress(ImportError, KeyError):
                for m in new_modules:
                    mod_path = getattr(sys.modules[m], '__file__', '')
                    if mod_path and mod_path.endswith('.pyi'):
                        continue
                    _reload_module(sys.modules[m])
        finally:
            typing.TYPE_CHECKING = False  # type: ignore[misc]
        module = sys.modules[modname]
    return module


def _find_type_stub_spec(
    spec: ModuleSpec, modname: str
) -> tuple[ModuleSpec, Path | None]:
    """Try finding a spec for a PEP 561 '.pyi' stub file for native modules."""
    if spec.origin is None:
        return spec, None

    for suffix in _NATIVE_SUFFIXES:
        if not spec.origin.endswith(suffix):
            continue
        pyi_path = Path(spec.origin.removesuffix(suffix) + '.pyi')
        if not pyi_path.is_file():
            continue
        pyi_loader = _StubFileLoader(modname, path=str(pyi_path))
        pyi_spec = spec_from_loader(modname, loader=pyi_loader)
        if pyi_spec is not None:
            return pyi_spec, pyi_path
    return spec, None


class _StubFileLoader(FileLoader):
    """Load modules from ``.pyi`` stub files."""

    def get_source(self, fullname: str) -> str:
        path = self.get_filename(fullname)
        for suffix in _NATIVE_SUFFIXES:
            if not path.endswith(suffix):
                continue
            path = path.removesuffix(suffix) + '.pyi'
        try:
            source_bytes = self.get_data(path)
        except OSError as exc:
            raise ImportError from exc
        return decode_source(source_bytes)


def _reload_module(module: ModuleType) -> Any:
    """Call importlib.reload(module), convert exceptions to ImportError"""
    try:
        return importlib.reload(module)
    except BaseException as exc:
        # Importing modules may cause any side effects, including
        # SystemExit, so we need to catch all errors.
        raise ImportError(exc, traceback.format_exc()) from exc


def import_object(
    modname: str,
    objpath: list[str],
    objtype: str = '',
    attrgetter: _AttrGetter = safe_getattr,
) -> Any:
    ret = _import_from_module_and_path(
        module_name=modname, obj_path=objpath, get_attr=attrgetter
    )
    if isinstance(ret, _ImportedObject):
        return [ret.module, ret.parent, ret.object_name, ret.obj]
    return None


def _import_from_module_and_path(
    *,
    module_name: str,
    obj_path: Sequence[str],
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject:
    obj_path = list(obj_path)
    if obj_path:
        logger.debug('[autodoc] from %s import %s', module_name, '.'.join(obj_path))
    else:
        logger.debug('[autodoc] import %s', module_name)

    module = None
    exc_on_importing = None
    try:
        while module is None:
            try:
                module = import_module(module_name, try_reload=True)
                logger.debug('[autodoc] import %s => %r', module_name, module)
            except ImportError as exc:
                logger.debug('[autodoc] import %s => failed', module_name)
                exc_on_importing = exc
                if '.' not in module_name:
                    raise

                # retry with parent module
                module_name, _, name = module_name.rpartition('.')
                obj_path.insert(0, name)

        obj = module
        parent = None
        object_name = ''
        for attr_name in obj_path:
            parent = obj
            logger.debug('[autodoc] getattr(_, %r)', attr_name)
            mangled_name = mangle(obj, attr_name)
            obj = get_attr(obj, mangled_name)

            try:
                logger.debug('[autodoc] => %r', obj)
            except TypeError:
                # fallback of failure on logging for broken object
                # See: https://github.com/sphinx-doc/sphinx/issues/9095
                logger.debug('[autodoc] => %r', (obj,))

            object_name = attr_name
        return _ImportedObject(
            module=module,
            parent=parent,
            object_name=object_name,
            obj=obj,
        )
    except (AttributeError, ImportError) as exc:
        if isinstance(exc, AttributeError) and exc_on_importing:
            # restore ImportError
            exc = exc_on_importing

        if obj_path:
            dotted_objpath = '.'.join(obj_path)
            err_parts = [
                f'autodoc: failed to import {dotted_objpath!r} '
                f'from module {module_name!r}'
            ]
        else:
            err_parts = [f'autodoc: failed to import {module_name!r}']

        if isinstance(exc, ImportError):
            # import_module() raises ImportError having real exception obj and
            # traceback
            real_exc = exc.args[0]
            traceback_msg = traceback.format_exception(exc)
            if isinstance(real_exc, SystemExit):
                err_parts.append(
                    'the module executes module level statement '
                    'and it might call sys.exit().'
                )
            elif isinstance(real_exc, ImportError) and real_exc.args:
                err_parts.append(
                    f'the following exception was raised:\n{real_exc.args[0]}'
                )
            else:
                err_parts.append(
                    f'the following exception was raised:\n{traceback_msg}'
                )
        else:
            err_parts.append(
                f'the following exception was raised:\n{traceback.format_exc()}'
            )

        errmsg = '; '.join(err_parts)
        logger.debug(errmsg)
        raise ImportError(errmsg) from exc


class Attribute(NamedTuple):
    name: str
    directly_defined: bool
    value: Any


def get_object_members(
    subject: Any,
    objpath: list[str],
    attrgetter: _AttrGetter,
    analyzer: ModuleAnalyzer | None = None,
) -> dict[str, Attribute]:
    """Get members and attributes of target object."""
    # the members directly defined in the class
    obj_dict = attrgetter(subject, '__dict__', {})

    members: dict[str, Attribute] = {}

    # enum members
    if isenumclass(subject):
        for name, defining_class, value in _filter_enum_dict(
            subject, attrgetter, obj_dict
        ):
            # the order of occurrence of *name* matches the subject's MRO,
            # allowing inherited attributes to be shadowed correctly
            if unmangled := unmangle(defining_class, name):
                members[unmangled] = Attribute(
                    name=unmangled,
                    directly_defined=defining_class is subject,
                    value=value,
                )

    # members in __slots__
    try:
        subject___slots__ = getslots(subject)
        if subject___slots__:
            for name in subject___slots__:
                members[name] = Attribute(
                    name=name, directly_defined=True, value=SLOTS_ATTR
                )
    except (TypeError, ValueError):
        pass

    # other members
    for name in dir(subject):
        try:
            value = attrgetter(subject, name)
            directly_defined = name in obj_dict
            unmangled = unmangle(subject, name)
            if unmangled and unmangled not in members:
                members[unmangled] = Attribute(
                    name=unmangled, directly_defined=directly_defined, value=value
                )
        except AttributeError:
            continue

    # annotation only member (ex. attr: int)
    for cls in getmro(subject):
        for name in getannotations(cls):
            unmangled = unmangle(cls, name)
            if unmangled and unmangled not in members:
                members[unmangled] = Attribute(
                    name=unmangled, directly_defined=cls is subject, value=INSTANCE_ATTR
                )

    if analyzer:
        # append instance attributes (cf. self.attr1) if analyzer knows
        namespace = '.'.join(objpath)
        for ns, name in analyzer.find_attr_docs():
            if namespace == ns and name not in members:
                members[name] = Attribute(
                    name=name, directly_defined=True, value=INSTANCE_ATTR
                )

    return members


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


def _import_data_declaration(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    type_aliases: dict[str, Any] | None,
) -> _ImportedObject | None:
    # annotation only instance variable (PEP-526)
    try:
        with mock(mock_imports):
            parent = import_module(module_name)
        annotations = get_type_hints(parent, None, type_aliases, include_extras=True)
        if obj_path[-1] in annotations:
            im = _ImportedObject(
                parent=parent,
                obj=UNINITIALIZED_ATTR,
            )
            return im
    except ImportError:
        pass
    return None


def _import_attribute_declaration(
    *,
    module_name: str,
    obj_path: Sequence[str],
    mock_imports: list[str],
    type_aliases: dict[str, Any] | None,
    get_attr: _AttrGetter = safe_getattr,
) -> _ImportedObject | None:
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
            return im
        elif _is_uninitialized_instance_attribute(
            parent=parent, obj_path=obj_path, type_aliases=type_aliases
        ):
            im = _ImportedObject(
                parent=parent,
                obj=UNINITIALIZED_ATTR,
            )
            return im
    except ImportError:
        pass
    return None


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


def _load_object_by_name(
    *,
    name: str,
    objtype: _AutodocObjType,
    mock_imports: list[str],
    type_aliases: dict[str, Any] | None,
    current_document: _CurrentDocument,
    env: BuildEnvironment,
    get_attr: _AttrGetter,
) -> tuple[_ItemProperties, str | None, str | None, ModuleType | None, Any] | None:
    # parse_name()

    # Determine what module to import and what attribute to document.
    #
    # Returns True and sets *self.modname*, *self.objpath*, *self.fullname*,
    # *self.args* and *self.retann* if parsing and resolving was successful.

    # first, parse the definition -- auto directives for classes and
    # functions can contain a signature which is then used instead of
    # an autogenerated one

    from sphinx.ext.autodoc import py_ext_sig_re

    matched = py_ext_sig_re.match(name)
    if matched is None:
        logger.warning(
            __('invalid signature for auto%s (%r)'),
            objtype,
            name,
            type='autodoc',
        )
        # need a module to import
        logger.warning(
            __(
                "don't know which module to import for autodocumenting "
                '%r (try placing a "module" or "currentmodule" directive '
                'in the document, or giving an explicit module name)'
            ),
            name,
            type='autodoc',
        )
        return None

    explicit_modname, path, base, _tp_list, args, retann = matched.groups()

    # support explicit module and class name separation via ::
    if explicit_modname is not None:
        module_name = explicit_modname.removesuffix('::')
        parents = path.rstrip('.').split('.') if path else []
    else:
        module_name = None
        parents = []

    with mock(mock_imports):
        resolved = _resolve_name(
            objtype=objtype,
            module_name=module_name,
            path=path,
            base=base,
            parents=parents,
            current_document=current_document,
            ref_context_py_module=env.ref_context.get('py:module'),
            ref_context_py_class=env.ref_context.get('py:class', ''),
        )
        if resolved is None:
            return None
        module_name, parts = resolved

    if objtype == 'module' and (args or retann):
        if args:
            msg = __("signature arguments given for automodule: '%s'")
            logger.warning(msg, name, type='autodoc')
            return None
        if retann:
            msg = __("return annotation given for automodule: '%s'")
            logger.warning(msg, name, type='autodoc')
            return None

    if not module_name:
        # need a module to import
        logger.warning(
            __(
                "don't know which module to import for autodocumenting "
                '%r (try placing a "module" or "currentmodule" directive '
                'in the document, or giving an explicit module name)'
            ),
            name,
            type='autodoc',
        )
        return None

    # now, import the module and get object to document

    props: _ItemProperties
    try:
        im = _import_object(
            module_name=module_name,
            obj_path=parts,
            mock_imports=mock_imports,
            get_attr=get_attr,
        )
    except ImportError as exc:
        if objtype == 'data':
            im_ = _import_data_declaration(
                module_name=module_name,
                obj_path=parts,
                mock_imports=mock_imports,
                type_aliases=type_aliases,
            )
        elif objtype == 'attribute':
            im_ = _import_attribute_declaration(
                module_name=module_name,
                obj_path=parts,
                mock_imports=mock_imports,
                type_aliases=type_aliases,
                get_attr=get_attr,
            )
        else:
            im_ = None
        if im_ is None:
            logger.warning(exc.args[0], type='autodoc', subtype='import_object')
            env.note_reread()
            return None
        else:
            im = im_

    module = im.module
    parent = im.parent
    object_name = im.object_name
    obj = im.obj

    obj_properties: set[_AutodocFuncProperty] = set()
    if objtype == 'module':
        file_path = getattr(module, '__file__', None)
        try:
            mod_all = inspect.getall(module)
        except ValueError:
            mod_all = None

        props = _ModuleProperties(
            obj_type=objtype,
            name=object_name,
            module_name=module_name,
            docstring_lines=(),
            file_path=Path(file_path) if file_path is not None else None,
            all=tuple(mod_all) if mod_all is not None else None,
            _obj=obj,
        )
    elif objtype in {'class', 'exception'}:
        if isinstance(obj, NewType | TypeVar):
            obj_module_name = getattr(obj, '__module__', module_name)
            if obj_module_name != module_name and module_name.startswith(
                obj_module_name
            ):
                bases = module_name[len(obj_module_name) :].strip('.').split('.')
                parts = tuple(bases) + parts
                module_name = obj_module_name

        props = _ClassDefProperties(
            obj_type=objtype,  # type: ignore[arg-type]
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            bases=getattr(obj, '__bases__', None),
            _obj=obj,
            _obj___name__=getattr(obj, '__name__', None),
        )
    elif objtype in {'function', 'decorator'}:
        if inspect.isstaticmethod(obj, cls=parent, name=object_name):
            obj_properties.add('staticmethod')
        if inspect.isclassmethod(obj):
            obj_properties.add('classmethod')

        props = _FunctionDefProperties(
            obj_type=objtype,  # type: ignore[arg-type]
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
        )
    elif objtype == 'method':
        # to distinguish classmethod/staticmethod
        obj_ = parent.__dict__.get(object_name, obj)
        if inspect.isstaticmethod(obj_, cls=parent, name=object_name):
            obj_properties.add('staticmethod')
        elif inspect.isclassmethod(obj_):
            obj_properties.add('classmethod')

        props = _FunctionDefProperties(
            obj_type=objtype,
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
        )
    elif objtype == 'property':
        if not inspect.isproperty(obj):
            # Support for class properties. Note: these only work on Python 3.9.
            __dict__ = safe_getattr(parent, '__dict__', {})
            obj = __dict__.get(parts[-1])
            if isinstance(obj, classmethod) and inspect.isproperty(obj.__func__):
                obj = obj.__func__
                obj_properties.add('classmethod')
            else:
                return None

        props = _FunctionDefProperties(
            obj_type=objtype,
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
        )
    elif objtype == 'data':
        # Update __annotations__ to support type_comment and so on
        annotations = dict(inspect.getannotations(parent))
        parent.__annotations__ = annotations

        try:
            analyzer = ModuleAnalyzer.for_module(module_name)
            analyzer.analyze()
            for (
                classname,
                attrname,
            ), annotation in analyzer.annotations.items():
                if not classname and attrname not in annotations:
                    annotations[attrname] = annotation
        except PycodeError:
            pass

        props = _AssignStatementProperties(
            obj_type=objtype,
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            value=...,
            annotation='',
            class_var=False,
            instance_var=False,
            _obj=obj,
        )
    elif objtype == 'attribute':
        if _is_slots_attribute(parent=parent, obj_path=parts):
            obj = SLOTS_ATTR
        elif inspect.isenumattribute(obj):
            obj = obj.value
        if parent:
            # Update __annotations__ to support type_comment and so on.
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

        props = _AssignStatementProperties(
            obj_type=objtype,
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            value=...,
            annotation='',
            class_var=False,
            instance_var=False,
            _obj=obj,
        )
    else:
        props = _ItemProperties(
            obj_type=objtype,
            name=object_name,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            _obj=obj,
        )

    return props, args, retann, module, parent


def _resolve_name(
    *,
    objtype: str,
    module_name: str | None,
    path: str | None,
    base: str,
    parents: Sequence[str],
    current_document: _CurrentDocument,
    ref_context_py_module: str | None,
    ref_context_py_class: str,
) -> tuple[str | None, tuple[str, ...]] | None:
    """Resolve the module and name of the object to document given by the
    arguments and the current module/class.

    Must return a pair of the module name and a chain of attributes; for
    example, it would return ``('zipfile', ('ZipFile', 'open'))`` for the
    ``zipfile.ZipFile.open`` method.
    """
    if objtype == 'module':
        if module_name is not None:
            logger.warning(
                __('"::" in automodule name doesn\'t make sense'), type='autodoc'
            )
        return (path or '') + base, ()

    if objtype in {'class', 'exception', 'function', 'decorator', 'data'}:
        if module_name is not None:
            return module_name, (*parents, base)
        if path:
            module_name = path.rstrip('.')
            return module_name, (*parents, base)

        # if documenting a toplevel object without explicit module,
        # it can be contained in another auto directive ...
        module_name = current_document.autodoc_module
        # ... or in the scope of a module directive
        if not module_name:
            module_name = ref_context_py_module
        # ... else, it stays None, which means invalid
        return module_name, (*parents, base)

    if objtype in {'method', 'property', 'attribute'}:
        if module_name is not None:
            return module_name, (*parents, base)

        if path:
            mod_cls = path.rstrip('.')
        else:
            # if documenting a class-level object without path,
            # there must be a current class, either from a parent
            # auto directive ...
            mod_cls = current_document.autodoc_class
            # ... or from a class directive
            if not mod_cls:
                mod_cls = ref_context_py_class
                # ... if still falsy, there's no way to know
                if not mod_cls:
                    return None, ()
        module_name, _sep, cls = mod_cls.rpartition('.')
        parents = [cls]
        # if the module name is still missing, get it like above
        if not module_name:
            module_name = current_document.autodoc_module
        if not module_name:
            module_name = ref_context_py_module
        # ... else, it stays None, which means invalid
        return module_name, (*parents, base)

    return None
