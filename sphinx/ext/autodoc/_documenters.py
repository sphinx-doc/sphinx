from __future__ import annotations

import sys
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
from sphinx.ext.autodoc._docstrings import _prepare_docstrings, _process_docstrings
from sphinx.ext.autodoc._member_finder import _document_members
from sphinx.ext.autodoc._renderer import _add_content, _directive_header_lines
from sphinx.ext.autodoc.mock import ismock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import safe_getattr
from sphinx.util.typing import restify, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from typing import Any, ClassVar, Final, Literal, NoReturn

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
        _TypeStatementProperties,
    )
    from sphinx.ext.autodoc.directive import DocumenterBridge
    from sphinx.util.typing import OptionSpec, _RestifyMode

logger = logging.getLogger('sphinx.ext.autodoc')


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
    #: true if the generated content may contain titles
    titles_allowed: ClassVar = True

    option_spec: ClassVar[OptionSpec] = {
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'noindex': bool_option,
    }

    def __init__(
        self, directive: DocumenterBridge, orig_name: str, indent: str = ''
    ) -> None:
        self.directive = directive
        self.config: Config = directive.env.config
        self.env: BuildEnvironment = directive.env
        self._current_document: _CurrentDocument = directive.env.current_document
        self._events: EventManager = directive.env.events
        self.options: _AutoDocumenterOptions = directive.genopt
        self.get_attr = directive.get_attr
        self.orig_name = orig_name
        self.indent: Final = indent
        # the module analyzer to get at attribute docs, or None
        self.analyzer: ModuleAnalyzer | None = None

        if isinstance(self, ModuleDocumenter):
            self.options = self.options.merge_member_options()
        elif isinstance(self, ClassDocumenter):
            if self.config.autodoc_class_signature == 'separated':
                # show __init__() method
                if self.options.special_members is None:
                    self.options.special_members = []
                self.options.special_members += ['__new__', '__init__']
            self.options = self.options.merge_member_options()

    def add_line(self, line: str, source: str, *lineno: int, indent: str) -> None:
        """Append one line of generated reST to the output."""
        if line.strip():  # not a blank line
            self.directive.result.append(indent + line, source, *lineno)
        else:
            self.directive.result.append('', source, *lineno)

    def add_directive_header(self, *, indent: str) -> None:
        """Add the directive header and options to the generated content."""
        domain_name = getattr(self, 'domain', 'py')
        if self.objtype in {'class', 'exception'} and self.props.doc_as_attr:  # type: ignore[attr-defined]
            directive_name = 'attribute'
        else:
            directive_name = getattr(self, 'directivetype', self.objtype)
        directive_name = f'{domain_name}:{directive_name}'

        if self.analyzer:
            is_final = self.props.dotted_parts in self.analyzer.finals
        else:
            is_final = False

        result = self.directive.result
        analyzer_source = '' if self.analyzer is None else self.analyzer.srcname
        source_name = _docstring_source_name(props=self.props, source=analyzer_source)
        for line in _directive_header_lines(
            autodoc_typehints=self.config.autodoc_typehints,
            directive_name=directive_name,
            is_final=is_final,
            options=self.options,
            props=self.props,
        ):
            if line.strip():  # not a blank line
                result.append(indent + line, source_name)
            else:
                result.append('', source_name)

    def add_content(self, more_content: StringList | None, *, indent: str) -> None:
        """Add content from docstrings, attribute documentation and user."""
        # add content from docstrings
        attr_docs = {} if self.analyzer is None else self.analyzer.attr_docs
        analyzer_source = '' if self.analyzer is None else self.analyzer.srcname
        processed_doc = StringList(
            list(
                _process_docstrings(
                    _prepare_docstrings(props=self.props, attr_docs=attr_docs),
                    events=self._events,
                    props=self.props,
                    obj=self.props._obj,
                    options=self.options,
                )
            ),
            source=_docstring_source_name(props=self.props, source=analyzer_source),
        )
        _add_content(
            processed_doc,
            result=self.directive.result,
            indent=indent + '   ',
        )

        # add additional content (e.g. from document), if present
        more_content = self._assemble_more_content(
            more_content=StringList() if more_content is None else more_content,
            typehints_format=self.config.autodoc_typehints_format,
            python_display_short_literal_types=self.config.python_display_short_literal_types,
            props=self.props,
        )
        _add_content(
            more_content,
            result=self.directive.result,
            indent=indent + '   ' * (self.props.obj_type != 'module'),
        )

    @staticmethod
    def _assemble_more_content(
        more_content: StringList,
        *,
        props: _ItemProperties,
        typehints_format: Literal['fully-qualified', 'short'],
        python_display_short_literal_types: bool,
    ) -> StringList:
        """Add content from docstrings, attribute documentation and user."""
        obj = props._obj

        if props.obj_type in {'data', 'attribute'}:
            mode = _get_render_mode(typehints_format)

            # Support for documenting GenericAliases
            if inspect.isgenericalias(obj):
                alias = restify(obj, mode=mode)
                more_content.append(_('alias of %s') % alias, '')
                more_content.append('', '')
            return more_content

        if props.obj_type in {'class', 'exception'}:
            from sphinx.ext.autodoc._property_types import _ClassDefProperties

            assert isinstance(props, _ClassDefProperties)

            mode = _get_render_mode(typehints_format)

            if isinstance(obj, NewType):
                supertype = restify(obj.__supertype__, mode=mode)
                return StringList([_('alias of %s') % supertype, ''], source='')

            if isinstance(obj, TypeVar):
                short_literals = python_display_short_literal_types
                attrs = [
                    repr(obj.__name__),
                    *(
                        stringify_annotation(
                            constraint, mode, short_literals=short_literals
                        )
                        for constraint in obj.__constraints__
                    ),
                ]
                if obj.__bound__:
                    attrs.append(rf'bound=\ {restify(obj.__bound__, mode=mode)}')
                if obj.__covariant__:
                    attrs.append('covariant=True')
                if obj.__contravariant__:
                    attrs.append('contravariant=True')

                alias = f'TypeVar({", ".join(attrs)})'
                return StringList([_('alias of %s') % alias, ''], source='')

            if props.doc_as_attr:
                try:
                    analyzer = ModuleAnalyzer.for_module(props.module_name)
                    analyzer.analyze()
                    key = ('', props.dotted_parts)
                    no_classvar_doc_comment = key not in analyzer.attr_docs
                except PycodeError:
                    no_classvar_doc_comment = True

                if no_classvar_doc_comment:
                    alias = restify(obj, mode=mode)
                    return StringList([_('alias of %s') % alias], source='')

            return more_content

        return more_content

    def _generate(
        self,
        more_content: StringList | None = None,
        real_modname: str | None = None,
        check_module: bool = False,
        all_members: bool = False,
    ) -> None:
        """Generate reST for the object given by *self.props*, and possibly for
        its members.

        If *more_content* is given, include that content. If *real_modname* is
        given, use that module name to find attribute docs. If *check_module* is
        True, only generate if the object is defined in the module name it is
        imported from. If *all_members* is True, document all members.
        """
        if self.props.obj_type in {'class', 'exception'}:
            # Do not pass real_modname and use the name from the __module__
            # attribute of the class.
            # If a class gets imported into the module real_modname
            # the analyzer won't find the source of the class, if
            # it looks in real_modname.
            real_modname = None

        # If there is no real module defined, figure out which to use.
        # The real module is used in the module analyzer to look up the module
        # where the attribute documentation would actually be found in.
        # This is used for situations where you have a module that collects the
        # functions and classes of internal submodules.
        guess_modname = self.props._obj___module__ or self.props.module_name
        self.real_modname: str = real_modname or guess_modname

        # try to also get a source code analyzer for attribute docs
        try:
            self.analyzer = ModuleAnalyzer.for_module(self.real_modname)
            # parse right now, to get PycodeErrors on parsing (results will
            # be cached anyway)
            self.analyzer.find_attr_docs()
        except PycodeError as exc:
            logger.debug('[autodoc] module analyzer failed: %s', exc)
            # no source file -- e.g. for builtin and C modules
            self.analyzer = None
            # at least add the module source file as a dependency
            if self.props.module_name:
                try:
                    module_spec = sys.modules[self.props.module_name].__spec__
                except (AttributeError, KeyError):
                    pass
                else:
                    if (
                        module_spec is not None
                        and module_spec.has_location
                        and module_spec.origin
                    ):
                        self.directive.record_dependencies.add(module_spec.origin)
        else:
            self.directive.record_dependencies.add(self.analyzer.srcname)

        if self.real_modname != guess_modname:
            # Add module to dependency list if target object is defined in other module.
            try:
                srcname = ModuleAnalyzer.for_module(guess_modname).srcname
                self.directive.record_dependencies.add(srcname)
            except PycodeError:
                pass

        has_docstring = any(self.props._docstrings or ())
        if ismock(self.props._obj) and not has_docstring:
            logger.warning(
                __('A mocked object is detected: %r'),
                self.props.full_name,
                type='autodoc',
                subtype='mocked_object',
            )

        # check __module__ of object (for members not given explicitly)
        if check_module and not self.options.imported_members:
            subject = inspect.unpartial(self.props._obj)
            modname = self.get_attr(subject, '__module__', None)
            if modname and modname != self.props.module_name:
                return

        indent = self.indent
        analyzer_source = '' if self.analyzer is None else self.analyzer.srcname
        source_name = _docstring_source_name(props=self.props, source=analyzer_source)

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.directive.result.append('', source_name)

        # generate the directive header and options, if applicable
        self.add_directive_header(indent=indent)
        self.directive.result.append('', source_name)

        # add all content (from docstrings, attribute docs etc.)
        self.add_content(more_content, indent=indent)

        # document members, if possible
        analyzer = self.analyzer
        if analyzer is not None:
            analyzer.analyze()
        _document_members(
            all_members=all_members,
            analyzer_order=analyzer.tagorder if analyzer is not None else {},
            attr_docs=analyzer.attr_docs if analyzer is not None else {},
            config=self.config,
            current_document=self._current_document,
            directive=self.directive,
            events=self._events,
            get_attr=self.get_attr,
            indent=indent,
            options=self.options,
            props=self.props,
            real_modname=self.real_modname,
            registry=self.env._registry,
        )


class ModuleDocumenter(Documenter):
    """Specialized Documenter subclass for modules."""

    props: _ModuleProperties

    objtype = 'module'

    option_spec: ClassVar[OptionSpec] = {
        'members': members_option,
        'undoc-members': bool_option,
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'inherited-members': inherited_members_option,
        'show-inheritance': bool_option,
        'synopsis': identity,
        'platform': identity,
        'deprecated': bool_option,
        'member-order': member_order_option,
        'exclude-members': exclude_members_option,
        'private-members': members_option,
        'special-members': members_option,
        'imported-members': bool_option,
        'ignore-module-all': bool_option,
        'no-value': bool_option,
        'noindex': bool_option,
    }


class FunctionDocumenter(Documenter):
    """Specialized Documenter subclass for functions."""

    props: _FunctionDefProperties

    objtype = 'function'


class DecoratorDocumenter(FunctionDocumenter):
    """Specialized Documenter subclass for decorator functions."""

    props: _FunctionDefProperties

    objtype = 'decorator'


class ClassDocumenter(Documenter):
    """Specialized Documenter subclass for classes."""

    props: _ClassDefProperties

    objtype = 'class'
    option_spec: ClassVar[OptionSpec] = {
        'members': members_option,
        'undoc-members': bool_option,
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'inherited-members': inherited_members_option,
        'show-inheritance': bool_option,
        'member-order': member_order_option,
        'exclude-members': exclude_members_option,
        'private-members': members_option,
        'special-members': members_option,
        'class-doc-from': class_doc_from_option,
        'noindex': bool_option,
    }


class ExceptionDocumenter(ClassDocumenter):
    """Specialized ClassDocumenter subclass for exceptions."""

    props: _ClassDefProperties

    objtype = 'exception'


class DataDocumenter(Documenter):
    """Specialized Documenter subclass for data items."""

    props: _AssignStatementProperties

    objtype = 'data'
    option_spec: ClassVar[OptionSpec] = dict(Documenter.option_spec)
    option_spec['annotation'] = annotation_option
    option_spec['no-value'] = bool_option


class MethodDocumenter(Documenter):
    """Specialized Documenter subclass for methods (normal, static and class)."""

    props: _FunctionDefProperties

    objtype = 'method'
    directivetype = 'method'


class AttributeDocumenter(Documenter):
    """Specialized Documenter subclass for attributes."""

    props: _AssignStatementProperties

    objtype = 'attribute'
    option_spec: ClassVar[OptionSpec] = dict(Documenter.option_spec)
    option_spec['annotation'] = annotation_option
    option_spec['no-value'] = bool_option


class PropertyDocumenter(Documenter):
    """Specialized Documenter subclass for properties."""

    props: _FunctionDefProperties

    objtype = 'property'


class TypeAliasDocumenter(Documenter):
    """Specialized Documenter subclass for type aliases."""

    props: _TypeStatementProperties

    objtype = 'type'
    option_spec: ClassVar[OptionSpec] = {
        'no-index': bool_option,
        'no-index-entry': bool_option,
        'annotation': annotation_option,
        'no-value': bool_option,
    }


class _AutodocAttrGetter:
    """getattr() override for types such as Zope interfaces."""

    _attr_getters: Sequence[tuple[type, Callable[[Any, str, Any], Any]]]

    __slots__ = ('_attr_getters',)

    def __init__(
        self, attr_getters: dict[type, Callable[[Any, str, Any], Any]], /
    ) -> None:
        super().__setattr__('_attr_getters', tuple(attr_getters.items()))

    def __call__(self, obj: Any, name: str, *defargs: Any) -> Any:
        for typ, func in self._attr_getters:
            if isinstance(obj, typ):
                return func(obj, name, *defargs)

        return safe_getattr(obj, name, *defargs)

    def __repr__(self) -> str:
        return f'_AutodocAttrGetter({dict(self._attr_getters)!r})'

    def __setattr__(self, key: str, value: Any) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)

    def __delattr__(self, key: str) -> NoReturn:
        msg = f'{self.__class__.__name__} is immutable'
        raise AttributeError(msg)


def _docstring_source_name(*, props: _ItemProperties, source: str) -> str:
    obj_module = inspect.safe_getattr(props._obj, '__module__', None)
    obj_qualname = inspect.safe_getattr(props._obj, '__qualname__', None)
    if obj_module and obj_qualname:
        # Get the correct location of docstring from props._obj
        # to support inherited methods
        fullname = f'{obj_module}.{obj_qualname}'
    else:
        fullname = props.full_name

    if source:
        return f'{source}:docstring of {fullname}'
    return f'docstring of {fullname}'
