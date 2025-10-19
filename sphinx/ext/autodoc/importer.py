"""Importer utilities for autodoc"""

from __future__ import annotations

import contextlib
import importlib
import itertools
import os
import re
import sys
import traceback
import typing
from importlib.abc import FileLoader
from importlib.machinery import EXTENSION_SUFFIXES
from importlib.util import decode_source, find_spec, module_from_spec, spec_from_loader
from inspect import Parameter, Signature
from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import TYPE_CHECKING, NewType, TypeVar
from weakref import WeakSet

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._docstrings import _get_docstring_lines
from sphinx.ext.autodoc._property_types import (
    _AssignStatementProperties,
    _ClassDefProperties,
    _FunctionDefProperties,
    _ItemProperties,
    _ModuleProperties,
    _TypeStatementProperties,
)
from sphinx.ext.autodoc._sentinels import (
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.mock import ismock, mock, undecorate
from sphinx.ext.autodoc.type_comment import update_annotations_using_type_comments
from sphinx.locale import __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.inspect import (
    _stringify_signature_to_parts,
    evaluate_signature,
    isclass,
    safe_getattr,
)
from sphinx.util.typing import get_type_hints, restify, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from importlib.machinery import ModuleSpec
    from typing import Any, Protocol, TypeAlias

    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment, _CurrentDocument
    from sphinx.events import EventManager
    from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
    from sphinx.ext.autodoc._property_types import _AutodocFuncProperty, _AutodocObjType

    _FormattedSignature: TypeAlias = tuple[str, str]

    class _AttrGetter(Protocol):
        def __call__(self, obj: Any, name: str, default: Any = ..., /) -> Any: ...


_NATIVE_SUFFIXES: frozenset[str] = frozenset({'.pyx', *EXTENSION_SUFFIXES})
logger = logging.getLogger(__name__)

_hide_value_re = re.compile(r'^:meta \s*hide-value:( +|$)')

#: extended signature RE: with explicit module name separated by ::
py_ext_sig_re = re.compile(
    r"""^ ([\w.]+::)?            # explicit module name
          ([\w.]+\.)?            # module and/or class name(s)
          (\w+)  \s*             # thing name
          (?: \[\s*(.*?)\s*])?   # optional: type parameters list
          (?: \((.*)\)           # optional: arguments
           (?:\s* -> \s* (.*))?  #           return annotation
          )? $                   # and nothing more
    """,
    re.VERBOSE,
)


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
) -> tuple[str, ...] | None:
    for cls in inspect.getmro(parent):
        try:
            module = safe_getattr(cls, '__module__')
            qualname = safe_getattr(cls, '__qualname__')

            analyzer = ModuleAnalyzer.for_module(module)
            analyzer.analyze()
            if qualname and obj_path:
                key = (qualname, attrname)
                if key in analyzer.attr_docs:
                    return tuple(analyzer.attr_docs[key])
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
    config: Config,
    env: BuildEnvironment,
    events: EventManager,
    get_attr: _AttrGetter,
    options: _AutoDocumenterOptions,
) -> tuple[_ItemProperties, ModuleType | None, Any] | None:
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
        if isinstance(obj, (NewType, TypeVar)):
            obj_module_name = getattr(obj, '__module__', module_name)
            if obj_module_name != module_name and module_name.startswith(
                obj_module_name
            ):
                bases = module_name[len(obj_module_name) :].strip('.').split('.')
                parts = tuple(bases) + parts
                module_name = obj_module_name

        if orig_bases := inspect.getorigbases(obj):
            # A subclass of generic types
            # refs: PEP-560 <https://peps.python.org/pep-0560/>
            obj_bases = list(orig_bases)
        elif hasattr(obj, '__bases__') and obj.__bases__:
            # A normal class
            obj_bases = list(obj.__bases__)
        else:
            obj_bases = []
        full_name = '.'.join((module_name, *parts))
        events.emit(
            'autodoc-process-bases',
            full_name,
            obj,
            SimpleNamespace(),
            obj_bases,
        )
        if config.autodoc_typehints_format == 'short':
            mode = 'smart'
        else:
            mode = 'fully-qualified-except-typing'
        base_classes = tuple(restify(cls, mode=mode) for cls in obj_bases)  # type: ignore[arg-type]

        props = _ClassDefProperties(
            obj_type=objtype,  # type: ignore[arg-type]
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            bases=getattr(obj, '__bases__', None),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
            _obj___name__=getattr(obj, '__name__', None),
            _obj___qualname__=getattr(obj, '__qualname__', None),
            _obj_bases=base_classes,
            _obj_is_new_type=isinstance(obj, NewType),
            _obj_is_typevar=isinstance(obj, TypeVar),
        )
    elif objtype in {'function', 'decorator'}:
        if inspect.isstaticmethod(obj, cls=parent, name=object_name):
            obj_properties.add('staticmethod')
        if inspect.isclassmethod(obj):
            obj_properties.add('classmethod')
        if inspect.iscoroutinefunction(obj) or inspect.isasyncgenfunction(obj):
            obj_properties.add('async')

        props = _FunctionDefProperties(
            obj_type=objtype,  # type: ignore[arg-type]
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
            _obj___name__=getattr(obj, '__name__', None),
            _obj___qualname__=getattr(obj, '__qualname__', None),
        )
    elif objtype == 'method':
        # to distinguish classmethod/staticmethod
        obj_ = parent.__dict__.get(object_name, obj)
        if inspect.isstaticmethod(obj_, cls=parent, name=object_name):
            obj_properties.add('staticmethod')
        elif (
            inspect.is_classmethod_like(obj_)
            or inspect.is_singledispatch_method(obj_)
            and inspect.is_classmethod_like(obj_.func)
        ):
            obj_properties.add('classmethod')
        if inspect.isabstractmethod(obj_):
            obj_properties.add('abstractmethod')
        if inspect.iscoroutinefunction(obj_) or inspect.isasyncgenfunction(obj_):
            obj_properties.add('async')

        props = _FunctionDefProperties(
            obj_type=objtype,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
            _obj___name__=getattr(obj, '__name__', None),
            _obj___qualname__=getattr(obj, '__qualname__', None),
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
        if inspect.isabstractmethod(obj):
            obj_properties.add('abstractmethod')

        # get property return type annotation
        obj_property_type_annotation = None
        if safe_getattr(obj, 'fget', None):  # property
            func = obj.fget  # type: ignore[union-attr]
        elif safe_getattr(obj, 'func', None):  # cached_property
            func = obj.func  # type: ignore[union-attr]
        else:
            func = None
        if func is not None:
            app = SimpleNamespace(config=config)
            # update the annotations of the property getter
            update_annotations_using_type_comments(app, func, False)  # type: ignore[arg-type]

            try:
                signature = inspect.signature(
                    func, type_aliases=config.autodoc_type_aliases
                )
            except TypeError as exc:
                full_name = '.'.join((module_name, *parts))
                logger.warning(
                    __('Failed to get a function signature for %s: %s'),
                    full_name,
                    exc,
                )
                pass
            except ValueError:
                pass
            else:
                if config.autodoc_typehints_format == 'short':
                    mode = 'smart'
                else:
                    mode = 'fully-qualified-except-typing'
                if signature.return_annotation is not Parameter.empty:
                    short_literals = config.python_display_short_literal_types
                    obj_property_type_annotation = stringify_annotation(
                        signature.return_annotation,
                        mode,  # type: ignore[arg-type]
                        short_literals=short_literals,
                    )

        props = _FunctionDefProperties(
            obj_type=objtype,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            properties=frozenset(obj_properties),
            _obj=obj,
            _obj___module__=get_attr(parent or obj, '__module__', None) or module_name,
            _obj___name__=getattr(parent or obj, '__name__', None),
            _obj___qualname__=getattr(parent or obj, '__qualname__', None),
            _obj_property_type_annotation=obj_property_type_annotation,
        )
    elif objtype == 'data':
        # Update __annotations__ to support type_comment and so on
        _ensure_annotations_from_type_comments(parent)

        # obtain annotation
        annotations = get_type_hints(
            parent,
            None,
            config.autodoc_type_aliases,
            include_extras=True,
        )
        if config.autodoc_typehints_format == 'short':
            mode = 'smart'
        else:
            mode = 'fully-qualified-except-typing'
        if parts[-1] in annotations:
            short_literals = config.python_display_short_literal_types
            type_annotation = stringify_annotation(
                annotations[parts[-1]],
                mode,  # type: ignore[arg-type]
                short_literals=short_literals,
            )
        else:
            type_annotation = None

        if (
            obj is RUNTIME_INSTANCE_ATTRIBUTE
            or obj is SLOTS_ATTR
            or obj is UNINITIALIZED_ATTR
        ):
            obj_sentinel = obj
        else:
            obj_sentinel = None

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
            _obj_is_generic_alias=inspect.isgenericalias(obj),
            _obj_is_attribute_descriptor=inspect.isattributedescriptor(obj),
            _obj_is_mock=ismock(obj),
            _obj_is_sentinel=obj_sentinel,
            _obj_repr_rst=inspect.object_description(obj),
            _obj_type_annotation=type_annotation,
        )
    elif objtype == 'attribute':
        if _is_slots_attribute(parent=parent, obj_path=parts):
            obj = SLOTS_ATTR
        elif inspect.isenumattribute(obj):
            obj = obj.value
        if parent:
            # Update __annotations__ to support type_comment and so on
            _ensure_annotations_from_type_comments(parent)

        # obtain annotation
        annotations = get_type_hints(
            parent,
            None,
            config.autodoc_type_aliases,
            include_extras=True,
        )
        if config.autodoc_typehints_format == 'short':
            mode = 'smart'
        else:
            mode = 'fully-qualified-except-typing'
        if parts[-1] in annotations:
            short_literals = config.python_display_short_literal_types
            type_annotation = stringify_annotation(
                annotations[parts[-1]],
                mode,  # type: ignore[arg-type]
                short_literals=short_literals,
            )
        else:
            type_annotation = None

        if (
            obj is RUNTIME_INSTANCE_ATTRIBUTE
            or obj is SLOTS_ATTR
            or obj is UNINITIALIZED_ATTR
        ):
            obj_sentinel = obj
        else:
            obj_sentinel = None

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
            _obj_is_generic_alias=inspect.isgenericalias(obj),
            _obj_is_attribute_descriptor=inspect.isattributedescriptor(obj),
            _obj_is_mock=ismock(obj),
            _obj_is_sentinel=obj_sentinel,
            _obj_repr_rst=inspect.object_description(obj),
            _obj_type_annotation=type_annotation,
        )
    elif objtype == 'type':
        obj_module_name = getattr(obj, '__module__', module_name)
        if obj_module_name != module_name and module_name.startswith(obj_module_name):
            bases = module_name[len(obj_module_name) :].strip('.').split('.')
            parts = tuple(bases) + parts
            module_name = obj_module_name

        if config.autodoc_typehints_format == 'short':
            mode = 'smart'
        else:
            mode = 'fully-qualified-except-typing'
        short_literals = config.python_display_short_literal_types
        ann = stringify_annotation(
            obj.__value__,
            mode,  # type: ignore[arg-type]
            short_literals=short_literals,
        )
        props = _TypeStatementProperties(
            obj_type=objtype,
            module_name=module_name,
            parts=parts,
            docstring_lines=(),
            _obj=obj,
            _obj___module__=get_attr(obj, '__module__', None),
            _obj___name__=getattr(obj, '__name__', None),
            _obj___qualname__=getattr(obj, '__qualname__', None),
            _obj___value__=ann,
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

    if options.class_doc_from is not None:
        class_doc_from = options.class_doc_from
    else:
        class_doc_from = config.autoclass_content
    props._docstrings = _get_docstring_lines(
        props,
        class_doc_from=class_doc_from,
        get_attr=get_attr,
        inherit_docstrings=config.autodoc_inherit_docstrings,
        parent=parent,
        tab_width=options._tab_width,
    )
    for line in itertools.chain.from_iterable(props._docstrings or ()):
        if _hide_value_re.match(line):
            props._docstrings_has_hide_value = True
            break

    # format the object's signature, if any
    try:
        signatures = _format_signatures(
            args=args,
            retann=retann,
            config=config,
            events=events,
            get_attr=get_attr,
            parent=parent,
            options=options,
            props=props,
        )
    except Exception as exc:
        msg = __('error while formatting signature for %s: %s')
        logger.warning(msg, props.full_name, exc, type='autodoc')
        return None
    props.signatures = tuple(
        f'{args} -> {retann}' if retann else str(args) for args, retann in signatures
    )

    return props, module, parent


def _parse_name(
    *,
    name: str,
    objtype: _AutodocObjType,
    current_document: _CurrentDocument,
    env: BuildEnvironment,
) -> tuple[str, tuple[str, ...], str | None, str | None] | None:
    """Parse *name* into module name, path, arguments, and return annotation."""
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
    if args is not None:
        args = f'({args})'

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
    objtype: _AutodocObjType,
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

    if objtype in {'class', 'exception', 'function', 'decorator', 'data', 'type'}:
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


_objects_with_type_comment_annotations: WeakSet[Any] = WeakSet()
"""Cache of objects with annotations updated from type comments."""


def _ensure_annotations_from_type_comments(obj: Any) -> None:
    """Ensures `obj.__annotations__` includes type comment information.

    Failures to assign to `__annotations__` are silently ignored.

    If `obj` is a class type, this also ensures that type comment
    information is incorporated into the `__annotations__` member of
    all parent classes, if possible.

    This mutates the `__annotations__` of existing imported objects,
    in order to allow the existing `typing.get_type_hints` method to
    take the modified annotations into account.

    Modifying existing imported objects is unfortunate but avoids the
    need to reimplement `typing.get_type_hints` in order to take into
    account type comment information.

    Note that this does not directly include type comment information
    from parent classes, but `typing.get_type_hints` takes that into
    account.
    """
    if obj in _objects_with_type_comment_annotations:
        return
    _objects_with_type_comment_annotations.add(obj)

    if isinstance(obj, type):
        for cls in inspect.getmro(obj):
            modname = safe_getattr(cls, '__module__')
            mod = sys.modules.get(modname)
            if mod is not None:
                _ensure_annotations_from_type_comments(mod)

    elif isinstance(obj, ModuleType):
        _update_module_annotations_from_type_comments(obj)


def _update_module_annotations_from_type_comments(mod: ModuleType) -> None:
    """Adds type comment annotations for a single module.

    Both module-level and class-level annotations are added.
    """
    mod_annotations = dict(inspect.getannotations(mod))
    mod.__annotations__ = mod_annotations

    class_annotations: dict[str, dict[str, Any]] = {}

    try:
        analyzer = ModuleAnalyzer.for_module(mod.__name__)
        analyzer.analyze()
        anns = analyzer.annotations
        for (classname, attrname), annotation in anns.items():
            if not classname:
                annotations = mod_annotations
            else:
                cls_annotations = class_annotations.get(classname)
                if cls_annotations is None:
                    try:
                        cls = mod
                        for part in classname.split('.'):
                            cls = safe_getattr(cls, part)
                        annotations = dict(inspect.getannotations(cls))
                        # Ignore errors setting __annotations__
                        with contextlib.suppress(TypeError, AttributeError):
                            cls.__annotations__ = annotations
                    except AttributeError:
                        annotations = {}
                    class_annotations[classname] = annotations
                else:
                    annotations = cls_annotations
            annotations.setdefault(attrname, annotation)
    except PycodeError:
        pass


def _format_signatures(
    *,
    config: Config,
    events: EventManager,
    get_attr: _AttrGetter,
    parent: Any,
    options: _AutoDocumenterOptions,
    props: _ItemProperties,
    args: str | None = None,
    retann: str | None = '',
    **kwargs: Any,
) -> list[_FormattedSignature]:
    """Format the signature (arguments and return annotation) of the object.

    Let the user process it via the ``autodoc-process-signature`` event.
    """
    if props.obj_type in {'class', 'exception'}:
        from sphinx.ext.autodoc._property_types import _ClassDefProperties

        assert isinstance(props, _ClassDefProperties)
        if props.doc_as_attr:
            return []
        if config.autodoc_class_signature == 'separated':
            # do not show signatures
            return []

    if config.autodoc_typehints_format == 'short':
        kwargs.setdefault('unqualified_typehints', True)
    if config.python_display_short_literal_types:
        kwargs.setdefault('short_literals', True)

    if args is None:
        signatures: list[_FormattedSignature] = []
    else:
        signatures = [(args, retann or '')]

    if (
        not signatures
        and config.autodoc_docstring_signature
        and props.obj_type not in {'module', 'data', 'type'}
    ):
        # only act if a signature is not explicitly given already,
        # and if the feature is enabled
        signatures[:] = _extract_signatures_from_docstring(
            config=config,
            get_attr=get_attr,
            options=options,
            parent=parent,
            props=props,
        )

    if not signatures:
        # try to introspect the signature
        try:
            signatures[:] = _extract_signature_from_object(
                config=config,
                events=events,
                get_attr=get_attr,
                parent=parent,
                props=props,
                **kwargs,
            )
        except Exception as exc:
            msg = __('error while formatting arguments for %s: %s')
            logger.warning(msg, props.full_name, exc, type='autodoc')

    if props.obj_type in {'attribute', 'property'}:
        # Only keep the return annotation
        signatures = [('', retann) for _args, retann in signatures]

    if result := events.emit_firstresult(
        'autodoc-process-signature',
        props.obj_type,
        props.full_name,
        props._obj,
        options,
        signatures[0][0] if signatures else None,  # args
        signatures[0][1] if signatures else '',  # retann
    ):
        if len(result) == 2 and isinstance(result[0], str):
            args, retann = result
            signatures[0] = (args, retann if isinstance(retann, str) else '')

    if props.obj_type in {'module', 'data', 'type'}:
        signatures[1:] = ()  # discard all signatures save the first

    if real_modname := props._obj___module__ or props.module_name:
        try:
            analyzer = ModuleAnalyzer.for_module(real_modname)
            # parse right now, to get PycodeErrors on parsing (results will
            # be cached anyway)
            analyzer.analyze()
        except PycodeError as exc:
            logger.debug('[autodoc] module analyzer failed: %s', exc)
            # no source file -- e.g. for builtin and C modules
            analyzer = None
    else:
        analyzer = None

    if props.obj_type in {'function', 'decorator'}:
        overloaded = (
            analyzer is not None
            and props.dotted_parts in analyzer.overloads
            and config.autodoc_typehints != 'none'
        )
        is_singledispatch = inspect.is_singledispatch_function(props._obj)

        if overloaded:
            # Use signatures for overloaded functions and methods instead of
            # their implementations.
            signatures.clear()
        elif not is_singledispatch:
            return signatures

        if is_singledispatch:
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            # append signature of singledispatch'ed functions
            for typ, func in props._obj.registry.items():
                if typ is object:
                    continue  # default implementation. skipped.
                dispatch_func = _annotate_to_first_argument(
                    func, typ, config=config, props=props
                )
                if not dispatch_func:
                    continue
                dispatch_props = _FunctionDefProperties(
                    obj_type='function',
                    module_name='',
                    parts=('',),
                    docstring_lines=(),
                    signatures=(),
                    _obj=dispatch_func,
                    _obj___module__=None,
                    _obj___qualname__=None,
                    _obj___name__=None,
                    properties=frozenset(),
                )
                signatures += _format_signatures(
                    config=config,
                    events=events,
                    get_attr=get_attr,
                    parent=None,
                    options=options,
                    props=dispatch_props,
                )
        if overloaded and analyzer is not None:
            actual = inspect.signature(
                props._obj, type_aliases=config.autodoc_type_aliases
            )
            obj_globals = safe_getattr(props._obj, '__globals__', {})
            overloads = analyzer.overloads[props.dotted_parts]
            for overload in overloads:
                overload = _merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, obj_globals, config.autodoc_type_aliases
                )
                signatures.append(_stringify_signature_to_parts(overload, **kwargs))

        return signatures

    if props.obj_type in {'class', 'exception'}:
        from sphinx.ext.autodoc._property_types import _ClassDefProperties

        assert isinstance(props, _ClassDefProperties)
        method_name = props._signature_method_name
        if method_name == '__call__':
            signature_cls = type(props._obj)
        else:
            signature_cls = props._obj
        overloads = []
        overloaded = False
        if method_name:
            for cls in signature_cls.__mro__:
                try:
                    analyzer = ModuleAnalyzer.for_module(cls.__module__)
                    analyzer.analyze()
                except PycodeError:
                    pass
                else:
                    qualname = f'{cls.__qualname__}.{method_name}'
                    if qualname in analyzer.overloads:
                        overloads = analyzer.overloads[qualname]
                        overloaded = True
                        break
                    if qualname in analyzer.tagorder:
                        # the constructor is defined in the class, but not overridden.
                        break
        if overloaded and config.autodoc_typehints != 'none':
            # Use signatures for overloaded methods instead of the implementation method.
            signatures.clear()
            method = safe_getattr(signature_cls, method_name, None)
            method_globals = safe_getattr(method, '__globals__', {})
            for overload in overloads:
                overload = evaluate_signature(
                    overload, method_globals, config.autodoc_type_aliases
                )

                parameters = list(overload.parameters.values())
                overload = overload.replace(
                    parameters=parameters[1:], return_annotation=Parameter.empty
                )
                signatures.append(_stringify_signature_to_parts(overload, **kwargs))
            return signatures

        return signatures

    if props.obj_type == 'method':
        overloaded = (
            analyzer is not None
            and props.dotted_parts in analyzer.overloads
            and config.autodoc_typehints != 'none'
        )
        meth = parent.__dict__.get(props.name)
        is_singledispatch = inspect.is_singledispatch_method(meth)

        if overloaded:
            # Use signatures for overloaded functions and methods instead of
            # their implementations.
            signatures.clear()
        elif not is_singledispatch:
            return signatures

        if is_singledispatch:
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            # append signature of singledispatch'ed methods
            for typ, func in meth.dispatcher.registry.items():
                if typ is object:
                    continue  # default implementation. skipped.
                if inspect.isclassmethod(func):
                    func = func.__func__
                dispatch_meth = _annotate_to_first_argument(
                    func, typ, config=config, props=props
                )
                if not dispatch_meth:
                    continue
                dispatch_props = _FunctionDefProperties(
                    obj_type='method',
                    module_name='',
                    parts=('',),
                    docstring_lines=(),
                    signatures=(),
                    _obj=dispatch_meth,
                    _obj___module__=None,
                    _obj___qualname__=None,
                    _obj___name__=None,
                    properties=frozenset(),
                )
                signatures += _format_signatures(
                    config=config,
                    events=events,
                    get_attr=get_attr,
                    parent=parent,
                    options=options,
                    props=dispatch_props,
                )
        if overloaded and analyzer is not None:
            from sphinx.ext.autodoc._property_types import _FunctionDefProperties

            assert isinstance(props, _FunctionDefProperties)
            actual = inspect.signature(
                props._obj,
                bound_method=not props.is_staticmethod,
                type_aliases=config.autodoc_type_aliases,
            )

            obj_globals = safe_getattr(props._obj, '__globals__', {})
            overloads = analyzer.overloads[props.dotted_parts]
            for overload in overloads:
                overload = _merge_default_value(actual, overload)
                overload = evaluate_signature(
                    overload, obj_globals, config.autodoc_type_aliases
                )

                if not props.is_staticmethod:
                    # hide the first argument (e.g. 'self')
                    parameters = list(overload.parameters.values())
                    overload = overload.replace(parameters=parameters[1:])
                signatures.append(_stringify_signature_to_parts(overload, **kwargs))

        return signatures

    return signatures


def _extract_signatures_from_docstring(
    config: Config,
    get_attr: _AttrGetter,
    options: _AutoDocumenterOptions,
    parent: Any,
    props: _ItemProperties,
) -> list[_FormattedSignature]:
    if props._docstrings is None:
        return []

    signatures: list[_FormattedSignature] = []

    # candidates of the object name
    valid_names = {props.name}
    if props.obj_type in {'class', 'exception'}:
        valid_names.add('__init__')
        if hasattr(props._obj, '__mro__'):
            valid_names |= {cls.__name__ for cls in props._obj.__mro__}

    docstrings = props._docstrings or ()
    _new_docstrings = [list(l) for l in docstrings]
    tab_width = options._tab_width
    for i, doclines in enumerate(docstrings):
        for j, line in enumerate(doclines):
            if not line:
                # no lines in docstring, no match
                break
            line = line.rstrip('\\').rstrip()

            # match first line of docstring against signature RE
            match = py_ext_sig_re.match(line)
            if not match:
                break
            _exmod, _path, base, _tp_list, args, retann = match.groups()
            if args is not None:
                args = f'({args})'
            else:
                args = ''  # i.e. property or attribute

            # the base name must match ours
            if base not in valid_names:
                break

            # re-prepare docstring to ignore more leading indentation
            _new_docstrings[i] = prepare_docstring(
                '\n'.join(doclines[j + 1 :]), tab_width
            )

            if props.obj_type in {'class', 'exception'} and retann == 'None':
                # Strip a return value from signatures of constructor in docstring
                signatures.append((args, ''))
            else:
                signatures.append((args, retann or ''))

        if signatures:
            # finish the loop when signature found
            break

    if not signatures:
        return []

    props._docstrings = _get_docstring_lines(
        props,
        class_doc_from=options.class_doc_from
        if options.class_doc_from is not None
        else config.autoclass_content,
        get_attr=get_attr,
        inherit_docstrings=config.autodoc_inherit_docstrings,
        parent=parent,
        tab_width=tab_width,
        _new_docstrings=tuple(tuple(doc) for doc in _new_docstrings),
    )

    return signatures


def _extract_signature_from_object(
    config: Config,
    events: EventManager,
    get_attr: _AttrGetter,
    parent: Any,
    props: _ItemProperties,
    **kwargs: Any,
) -> list[_FormattedSignature]:
    """Format the signature using runtime introspection."""
    sig = _get_signature_object(
        events=events,
        get_attr=get_attr,
        parent=parent,
        props=props,
        type_aliases=config.autodoc_type_aliases,
    )
    if sig is None:
        return []

    if props.obj_type == 'decorator' and len(sig.parameters) == 1:
        # Special case for single-argument decorators
        return [('', '')]

    if config.autodoc_typehints in {'none', 'description'}:
        kwargs.setdefault('show_annotation', False)
    if config.autodoc_typehints_format == 'short':
        kwargs.setdefault('unqualified_typehints', True)
    if config.python_display_short_literal_types:
        kwargs.setdefault('short_literals', True)
    if props.obj_type in {'class', 'exception'}:
        kwargs['show_return_annotation'] = False

    args, retann = _stringify_signature_to_parts(sig, **kwargs)
    if config.strip_signature_backslash:
        # escape backslashes for reST
        args = args.replace('\\', '\\\\')
        retann = retann.replace('\\', '\\\\')

    return [(args, retann)]


# Types which have confusing metaclass signatures it would be best not to show.
# These are listed by name, rather than storing the objects themselves, to avoid
# needing to import the modules.
_METACLASS_CALL_BLACKLIST = frozenset({
    'enum.EnumType.__call__',
})


# Types whose __new__ signature is a pass-through.
_CLASS_NEW_BLACKLIST = frozenset({
    'typing.Generic.__new__',
})


def _get_signature_object(
    events: EventManager,
    get_attr: _AttrGetter,
    parent: Any,
    props: _ItemProperties,
    type_aliases: Mapping[str, str] | None,
) -> Signature | None:
    """Return a Signature for *obj*, or None on failure."""
    obj = props._obj
    if props.obj_type in {'function', 'decorator'}:
        events.emit('autodoc-before-process-signature', obj, False)
        try:
            return inspect.signature(obj, type_aliases=type_aliases)
        except TypeError as exc:
            msg = __('Failed to get a function signature for %s: %s')
            logger.warning(msg, props.full_name, exc)
            return None
        except ValueError:
            return None

    if props.obj_type in {'class', 'exception'}:
        if isinstance(obj, (NewType, TypeVar)):
            # Suppress signature
            return None

        try:
            object_sig = obj.__signature__
        except AttributeError:
            pass
        else:
            if isinstance(object_sig, Signature):
                return object_sig
            if sys.version_info[:2] in {(3, 12), (3, 13)} and callable(object_sig):
                # Support for enum.Enum.__signature__ in Python 3.12
                if isinstance(object_sig_str := object_sig(), str):
                    return inspect.signature_from_str(object_sig_str)

        def get_user_defined_function_or_method(obj: Any, attr: str) -> Any:
            """Get the `attr` function or method from `obj`, if it is user-defined."""
            if inspect.is_builtin_class_method(obj, attr):
                return None
            attr = get_attr(obj, attr, None)
            if not (inspect.ismethod(attr) or inspect.isfunction(attr)):
                return None
            return attr

        # This sequence is copied from inspect._signature_from_callable.
        # ValueError means that no signature could be found, so we keep going.

        # Let's see if it has an overloaded __call__ defined in its metaclass,
        # or if the 'obj' class has a '__new__' or '__init__' method
        for obj_, meth_name, blacklist in (
            (type(obj), '__call__', _METACLASS_CALL_BLACKLIST),
            (obj, '__new__', _CLASS_NEW_BLACKLIST),
            (obj, '__init__', frozenset()),
        ):
            meth = get_user_defined_function_or_method(obj_, meth_name)
            if meth is None:
                continue
            if blacklist:
                if f'{meth.__module__}.{meth.__qualname__}' in blacklist:
                    continue

            events.emit('autodoc-before-process-signature', meth, True)
            try:
                object_sig = inspect.signature(
                    meth,
                    bound_method=True,
                    type_aliases=type_aliases,
                )
            except TypeError as exc:
                msg = __('Failed to get a constructor signature for %s: %s')
                logger.warning(msg, props.full_name, exc)
                return None
            except ValueError:
                continue
            else:
                from sphinx.ext.autodoc._property_types import _ClassDefProperties

                assert isinstance(props, _ClassDefProperties)
                props._signature_method_name = meth_name
                return object_sig

        # None of the attributes are user-defined, so fall back to let inspect
        # handle it.
        # We don't know the exact method that inspect.signature will read
        # the signature from, so just pass the object itself to our hook.
        events.emit('autodoc-before-process-signature', obj, False)
        try:
            return inspect.signature(
                obj,
                bound_method=False,
                type_aliases=type_aliases,
            )
        except TypeError as exc:
            msg = __('Failed to get a constructor signature for %s: %s')
            logger.warning(msg, props.full_name, exc)
            return None
        except ValueError:
            pass

        # Still no signature: happens e.g. for old-style classes
        # with __init__ in C and no `__text_signature__`.
        return None

    if props.obj_type == 'method':
        if obj == object.__init__ and parent != object:  # NoQA: E721
            # Classes not having own __init__() method are shown as no arguments.
            #
            # Note: The signature of object.__init__() is (self, /, *args, **kwargs).
            #       But it makes users confused.
            return Signature()

        is_bound_method = not inspect.isstaticmethod(
            obj, cls=parent, name=props.object_name
        )
        events.emit('autodoc-before-process-signature', obj, is_bound_method)
        try:
            return inspect.signature(
                obj, bound_method=is_bound_method, type_aliases=type_aliases
            )
        except TypeError as exc:
            msg = __('Failed to get a method signature for %s: %s')
            logger.warning(msg, props.full_name, exc)
            return None
        except ValueError:
            return None

    return None


def _annotate_to_first_argument(
    func: Callable[..., Any], typ: type, *, config: Config, props: _ItemProperties
) -> Callable[..., Any] | None:
    """Annotate type hint to the first argument of function if needed."""
    try:
        sig = inspect.signature(func, type_aliases=config.autodoc_type_aliases)
    except TypeError as exc:
        msg = __('Failed to get a function signature for %s: %s')
        logger.warning(msg, props.full_name, exc)
        return None
    except ValueError:
        return None

    first_arg_idx = 1 * (props.obj_type == 'method')
    if len(sig.parameters) == first_arg_idx:
        return None

    def dummy():  # type: ignore[no-untyped-def]  # NoQA: ANN202
        pass

    params = list(sig.parameters.values())
    if params[first_arg_idx].annotation is Parameter.empty:
        params[first_arg_idx] = params[first_arg_idx].replace(annotation=typ)
        try:
            dummy.__signature__ = sig.replace(parameters=params)  # type: ignore[attr-defined]
            return dummy
        except (AttributeError, TypeError):
            # failed to update signature (ex. built-in or extension types)
            return None

    return func


def _merge_default_value(actual: Signature, overload: Signature) -> Signature:
    """Merge default values of actual implementation to the overload variants."""
    parameters = list(overload.parameters.values())
    for i, param in enumerate(parameters):
        actual_param = actual.parameters.get(param.name)
        if actual_param and param.default == '...':
            parameters[i] = param.replace(default=actual_param.default)

    return overload.replace(parameters=parameters)
