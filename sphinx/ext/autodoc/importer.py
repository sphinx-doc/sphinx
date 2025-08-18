"""Importer utilities for autodoc"""

from __future__ import annotations

import contextlib
import importlib
import os
import sys
import traceback
import typing
from importlib.abc import FileLoader
from importlib.machinery import EXTENSION_SUFFIXES
from importlib.util import decode_source, find_spec, module_from_spec, spec_from_loader
from pathlib import Path
from typing import TYPE_CHECKING, NewType, TypeVar

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._property_types import (
    _AssignStatementProperties,
    _ClassDefProperties,
    _FunctionDefProperties,
    _ItemProperties,
    _ModuleProperties,
)
from sphinx.ext.autodoc._sentinels import (
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.mock import ismock, mock, undecorate
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import (
    isclass,
    safe_getattr,
)
from sphinx.util.typing import get_type_hints

if TYPE_CHECKING:
    from collections.abc import Sequence
    from importlib.machinery import ModuleSpec
    from types import ModuleType
    from typing import Any, Protocol

    from sphinx.environment import BuildEnvironment, _CurrentDocument
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


def mangle(subject: Any, name: str) -> str:
    """Mangle the given name."""
    try:
        if isclass(subject) and name.startswith('__') and not name.endswith('__'):
            return f'_{subject.__name__}{name}'
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
    """Import and load the object given by *name*."""
    parsed = _parse_name(
        name=name,
        objtype=objtype,
        current_document=current_document,
        env=env,
    )
    if parsed is None:
        return None
    module_name, parts, args, retann = parsed

    # Import the module and get the object to document
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

    # Assemble object properties from the imported object.
    props: _ItemProperties
    module = im.module
    parent = im.parent
    object_name = im.object_name
    obj = im.obj
    obj_properties: set[_AutodocFuncProperty] = set()
    if objtype == 'module':
        file_path = getattr(module, '__file__', None)
        mod_all = safe_getattr(obj, '__all__', None)
        if isinstance(mod_all, (list, tuple)) and all(
            isinstance(e, str) for e in mod_all
        ):
            mod_all = tuple(mod_all)
        elif mod_all is not None:
            # Invalid __all__ found.
            msg = __('Ignoring invalid __all__ in module %s: %r')
            logger.warning(msg, module_name, mod_all, type='autodoc')
            mod_all = None

        props = _ModuleProperties(
            obj_type=objtype,
            module_name=module_name,
            docstring_lines=(),
            file_path=Path(file_path) if file_path is not None else None,
            all=mod_all,
            _obj=obj,
            _obj___module__=obj.__name__,
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
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            bases=getattr(obj, '__bases__', None),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
            _obj___name__=getattr(obj, '__name__', None),
        )
    elif objtype in {'function', 'decorator'}:
        if inspect.isstaticmethod(obj, cls=parent, name=object_name):
            obj_properties.add('staticmethod')
        if inspect.isclassmethod(obj):
            obj_properties.add('classmethod')

        props = _FunctionDefProperties(
            obj_type=objtype,  # type: ignore[arg-type]
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
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
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
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
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
            _obj___module__=get_attr(parent or obj, '__module__', None) or module_name,
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
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            value=...,
            annotation='',
            class_var=False,
            instance_var=False,
            _obj=obj,
            _obj___module__=get_attr(parent or obj, '__module__', None) or module_name,
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
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            value=...,
            annotation='',
            class_var=False,
            instance_var=False,
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
        )
    else:
        props = _ItemProperties(
            obj_type=objtype,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
        )

    return props, args, retann, module, parent


def _parse_name(
    *,
    name: str,
    objtype: _AutodocObjType,
    current_document: _CurrentDocument,
    env: BuildEnvironment,
) -> tuple[str, tuple[str, ...], str | None, str | None] | None:
    """Parse *name* into module name, path, arguments, and return annotation."""
    from sphinx.ext.autodoc._documenters import py_ext_sig_re

    # Parse the definition in *name*.
    # autodoc directives for classes and functions can contain a signature,
    # which overrides the autogenerated one.
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

    # Support explicit module and class name separation via ``::``
    if explicit_modname is not None:
        module_name = explicit_modname.removesuffix('::')
        parents = path.rstrip('.').split('.') if path else ()
    else:
        module_name = None
        parents = ()

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
        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)
    module_name, parts = resolved

    if objtype == 'module' and args:
        msg = __("signature arguments given for automodule: '%s'")
        logger.warning(msg, name, type='autodoc')
        return None
    if objtype == 'module' and retann:
        msg = __("return annotation given for automodule: '%s'")
        logger.warning(msg, name, type='autodoc')
        return None

    if not module_name:
        # Could not resolve a module to import
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

    return module_name, parts, args, retann


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
