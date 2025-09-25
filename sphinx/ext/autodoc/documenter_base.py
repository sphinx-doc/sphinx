from __future__ import annotations

import functools
import operator
import re
import sys
from inspect import Parameter, Signature
from typing import TYPE_CHECKING, NewType, TypeVar

from docutils.statemachine import StringList

from sphinx.errors import PycodeError
from sphinx.ext.autodoc._directive_options import (
    annotation_option,
    bool_option,
    class_doc_from_option,
    exclude_members_option,
    identity,
    inherited_members_option,
    member_order_option,
    members_option,
)
from sphinx.ext.autodoc._member_finder import _filter_members, _get_members_to_document
from sphinx.ext.autodoc._sentinels import (
    ALL,
    RUNTIME_INSTANCE_ATTRIBUTE,
    SLOTS_ATTR,
    SUPPRESS,
    UNINITIALIZED_ATTR,
)
from sphinx.ext.autodoc.importer import (
    _get_attribute_comment,
    _is_runtime_instance_attribute_not_commented,
    _load_object_by_name,
    _resolve_name,
)
from sphinx.ext.autodoc.mock import ismock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.docstrings import prepare_docstring, separate_metadata
from sphinx.util.inspect import (
    evaluate_signature,
    getdoc,
    object_description,
    safe_getattr,
    stringify_signature,
)
from sphinx.util.typing import get_type_hints, restify, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence
    from types import ModuleType
    from typing import Any, ClassVar, Literal

    from sphinx.config import Config
    from sphinx.environment import BuildEnvironment, _CurrentDocument
    from sphinx.events import EventManager
    from sphinx.ext.autodoc._directive_options import _AutoDocumenterOptions
    from sphinx.ext.autodoc._property_types import (
        _AssignStatementProperties,
        _ClassDefProperties,
        _FunctionDefProperties,
        _ItemProperties,
        _ModuleProperties,
    )
    from sphinx.ext.autodoc.directive import DocumenterBridge
    from sphinx.registry import SphinxComponentRegistry
    from sphinx.util.typing import OptionSpec, _RestifyMode

logger = logging.getLogger('sphinx.ext.autodoc')

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


def _get_render_mode(
    typehints_format: Literal['fully-qualified', 'short'],
) -> _RestifyMode:
    if typehints_format == 'short':
        return 'smart'
    return 'fully-qualified-except-typing'


class Documenter:
    """A Documenter knows how to autodocument a single object type.  When
    registered with the AutoDirective, it will be used to document objects
    of that type when needed by autodoc.

    Its *objtype* attribute selects what auto directive it is assigned to
    (the directive name is 'auto' + objtype), and what directive it generates
    by default, though that can be overridden by an attribute called
    *directivetype*.

    A Documenter has an *option_spec* that works like a docutils directive's;
    in fact, it will be used to parse an auto directive's options that matches
    the Documenter.
    """

    props: _ItemProperties

    #: name by which the directive is called (auto...) and the default
    #: generated directive name
    objtype: ClassVar = 'object'
    #: indentation by which to indent the directive content
    content_indent: ClassVar = '   '
    #: priority if multiple documenters return True from can_document_member
    priority: ClassVar = 0
    #: order if autodoc_member_order is set to 'groupwise'
    member_order: ClassVar = 0
    #: true if the generated content may contain titles
    titles_allowed: ClassVar = True

    __docstring_signature__: ClassVar[bool] = False
    """If True, attempt to read the signature from the docstring."""

    __docstring_strip_signature__: ClassVar[bool] = False
    """If True, strip any function signature from the docstring."""

    __uninitialized_global_variable__: ClassVar[bool] = False
    """If True, support uninitialized (type annotation only) global variables"""

    _new_docstrings: list[list[str]] | None = None
    _signatures: list[str] = []

    option_spec: ClassVar[OptionSpec] = {
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'noindex': bool_option,
    }

    def get_attr(self, obj: Any, name: str, *defargs: Any) -> Any:
        """getattr() override for types such as Zope interfaces."""
        return autodoc_attrgetter(obj, name, *defargs, registry=self.env._registry)

    @classmethod
    def can_document_member(
        cls: type[Documenter], member: Any, membername: str, isattr: bool, parent: Any
    ) -> bool:
        """Called to see if a member can be documented by this Documenter."""
        msg = 'must be implemented in subclasses'
        raise NotImplementedError(msg)

    def __init__(
        self, directive: DocumenterBridge, name: str, indent: str = ''
    ) -> None:
        self.directive = directive
        self.config: Config = directive.env.config
        self.env: BuildEnvironment = directive.env
        self._current_document: _CurrentDocument = directive.env.current_document
        self._events: EventManager = directive.env.events
        self.options: _AutoDocumenterOptions = directive.genopt
        self.name = name
        self.indent = indent
        # the module and object path within the module, and the fully
        # qualified name (all set after resolve_name succeeds)
        self.modname: str = ''
        self.module: ModuleType | None = None
        self.objpath: list[str] = []
        self.fullname = ''
        # extra signature items (arguments and return annotation,
        # also set after resolve_name succeeds)
        self.args: str | None = None
        self.retann: str | None = ''
        # the object to document (set after import_object succeeds)
        self.object: Any = None
        self.object_name = ''
        # the parent/owner of the object to document
        self.parent: Any = None
        # the module analyzer to get at attribute docs, or None
        self.analyzer: ModuleAnalyzer | None = None

        self._load_object_has_been_called = False
        # Lazy loading cache for members
        self._members_cache: dict[str, Any] = {}
        self._members_loaded = False

    def _lazy_load_members(self) -> dict[str, Any]:
        """Lazy load members only when needed."""
        if self._members_loaded:
            return self._members_cache

        # Import the member finder functions only when needed
        from sphinx.ext.autodoc._member_finder import _get_members_to_document

        # Get members for this object
        members = _get_members_to_document(
            self.object,
            self.object_name,
            self.options,
            self.config.autodoc_member_order,
            self.env._registry.documenters,
            self.env._registry.filters,
        )

        self._members_cache = members
        self._members_loaded = True
        return members

    @property
    def documenters(self) -> dict[str, type[Documenter]]:
        """Returns registered Documenter classes"""
        return self.env._registry.documenters

    def add_line(self, line: str, source: str, *lineno: int) -> None:
        """Append one line of generated reST to the output."""
        if line.strip():  # not a blank line
            self.directive.result.append(self.indent + line, source, *lineno)
        else:
            self.directive.result.append('', source, *lineno)

    def _load_object_by_name(self) -> Literal[True] | None:
        if self._load_object_has_been_called:
            return True

        # Check if this object was already loaded by a previous documenter
        from sphinx.ext.autodoc.importer import _get_cached_module_info
        cache_key = f"{self.name}:{self.objtype}"
        cached_info = _get_cached_module_info(cache_key)
        if cached_info:
            props, args, retann, module, parent = cached_info['object_info']
            self.props = props
            self.args = args
            self.retann = retann
            self.modname = props.module_name
            self.objpath = list(props.parts)
            self.fullname = props.full_name
            self.module = module
            self.parent = parent
            self.object_name = props.object_name
            self.object = props._obj
            self._load_object_has_been_called = True
            return True

        ret = _load_object_by_name(
            name=self.name,
            objtype=self.objtype,
            mock_imports=self.config.autodoc_mock_imports,
            type_aliases=self.config.autodoc_type_aliases,
            current_document=self._current_document,
            env=self.env,
            get_attr=self.get_attr,
        )
        if ret is None:
            return None
        props, args, retann, module, parent = ret

        self.props = props
        self.args = args
        self.retann = retann
        self.modname = props.module_name
        self.objpath = list(props.parts)
        self.fullname = props.full_name
        self.module = module
        self.parent = parent
        self.object_name = props.object_name
        self.object = props._obj

        # Cache the loaded object for future documenters
        from sphinx.ext.autodoc.importer import _cache_module_info
        _cache_module_info(cache_key, {'object_info': ret})
        if self.objtype == 'method':
            if 'staticmethod' in props.properties:  # type: ignore[attr-defined]
                # document static members before regular methods
                self.member_order -= 1  # type: ignore[misc]
            elif 'classmethod' in props.properties:  # type: ignore[attr-defined]
                # document class methods before static methods as
                # they usually behave as alternative constructors
                self.member_order -= 2  # type: ignore[misc]
        self._load_object_has_been_called = True
        return True

    def resolve_name(
        self, modname: str | None, parents: Any, path: str, base: str
    ) -> tuple[str | None, list[str]]:
        """Resolve the module and name of the object to document given by the
        arguments and the current module/class.

        Must return a pair of the module name and a chain of attributes; for
        example, it would return ``('zipfile', ['ZipFile', 'open'])`` for the
        ``zipfile.ZipFile.open`` method.
        """
        ret = _resolve_name(
            objtype=self.objtype,
            modname=modname,
            parents=parents,
            path=path,
            base=base,
        )
        self.modname, self.objpath = ret
        return ret

    def parse_name(self, name: str, arguments: str) -> None:
        """Parse the name into ``self.modname`` and ``self.objpath``."""
        if name:
            self.modname, self.objpath = _resolve_name(
                objtype=self.objtype,
                modname=None,
                parents=None,
                path=name,
                base='',
            )
        if arguments:
            self.args = arguments

    def import_object(self, level: int = 0) -> bool:
        """Import the object given by ``self.modname`` and ``self.objpath``."""
        if not self._load_object_by_name():
            return False
        return True

    def get_object_members(self, want_all: bool, **kwargs: bool) -> dict[str, Any]:
        """Return ``(members_check_function, members)`` where ``members`` is a
        list of ``(membername, member)`` pairs of the members of ``self.object``.

        If ``want_all`` is True, return all members.  Otherwise, only return
        those matching the ``**kwargs``.
        """
        return _filter_members(
            self.object,
            self.object_name,
            self.options,
            self.config.autodoc_member_order,
            self.env._registry.filters,
            want_all,
            **kwargs,
        )

    def filter_members(
        self,
        members: dict[str, Any],
        want_all: bool,
        **kwargs: bool,
    ) -> dict[str, Any]:
        """Filter the given member list.

        Members are filtered by the ``**kwargs``, and ``want_all`` is a
        flag indicating if all members should be returned regardless of the
        ``**kwargs`` values.

        If ``want_all`` is True, return all members.  Otherwise, only return
        those matching the ``**kwargs``.
        """
        return _filter_members(
            self.object,
            self.object_name,
            self.options,
            self.config.autodoc_member_order,
            self.env._registry.filters,
            want_all,
            **kwargs,
        )

    def get_doc(self, clean_doc: bool = True) -> list[str]:
        """Decode and return lines of the docstring(s) for the object."""
        docstrings = self.get_docstring()
        if docstrings is None:
            return []
        return docstrings

    def get_docstring(self) -> list[str] | None:
        """Returns the docstring of the object."""
        if not self.object:
            return None
        return getdoc(self.object, clean=True, clean_doc=self.config.autodoc_docstring_signature)

    def get_object_type(self) -> str:
        """Return the type of the object as a string."""
        return object_description(self.object)

    def add_content(self, more_content: Any, **kwargs: Any) -> None:
        """Add content from docstrings and user."""
        pass

    def add_directive_header(self, sig: str) -> None:
        """Add the directive header and options."""
        pass

    def add_target_and_index(self, name: str, sig: str, signode: Any) -> None:
        """Add cross-reference target and index entry."""
        pass

    def get_signatures(self) -> list[str]:
        """Return the signatures of the object."""
        return self._signatures

    def get_docstring_signature(self) -> tuple[str, str] | None:
        """Return the signature from the docstring."""
        return None

    def generate(
        self,
        more_content: Any = None,
        real_modname: str | None = None,
        real_objname: str | None = None,
        allow_inherited: bool = True,
        **kwargs: Any,
    ) -> str:
        """Generate the reST text for the object."""
        return ''

    def document_members(self, want_all: bool = True, **kwargs: Any) -> None:
        """Generate reST for the members of the object."""
        pass

    def record_dependencies(self) -> None:
        """Record dependencies."""
        pass


# Define __all__ for this module
__all__ = ['Documenter', '_get_render_mode', 'py_ext_sig_re']
