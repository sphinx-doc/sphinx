from __future__ import annotations

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
from sphinx.ext.autodoc._member_finder import _gather_members
from sphinx.ext.autodoc._renderer import _add_content, _directive_header_lines
from sphinx.ext.autodoc._sentinels import ALL
from sphinx.ext.autodoc.importer import _load_object_by_name
from sphinx.ext.autodoc.mock import ismock
from sphinx.locale import _, __
from sphinx.pycode import ModuleAnalyzer
from sphinx.util import inspect, logging
from sphinx.util.inspect import safe_getattr
from sphinx.util.typing import restify, stringify_annotation

if TYPE_CHECKING:
    from collections.abc import Iterator
    from types import ModuleType
    from typing import Any, ClassVar, Final, Literal

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
    from sphinx.registry import SphinxComponentRegistry
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

    def get_attr(self, obj: Any, name: str, *defargs: Any) -> Any:
        """getattr() override for types such as Zope interfaces."""
        return autodoc_attrgetter(obj, name, *defargs, registry=self.env._registry)

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
        self.indent: Final = indent
        self.module: ModuleType | None = None
        # the parent/owner of the object to document
        self.parent: Any = None
        # the module analyzer to get at attribute docs, or None
        self.analyzer: ModuleAnalyzer | None = None

        self._load_object_has_been_called = False

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

    def _load_object_by_name(self) -> Literal[True] | None:
        """Import the object given by *self.name*.

        Returns True if parsing and resolving was successful, otherwise None.
        """
        if self._load_object_has_been_called:
            return True

        ret = _load_object_by_name(
            name=self.name,
            objtype=self.objtype,  # type: ignore[arg-type]
            mock_imports=self.config.autodoc_mock_imports,
            type_aliases=self.config.autodoc_type_aliases,
            current_document=self._current_document,
            config=self.config,
            env=self.env,
            events=self._events,
            get_attr=self.get_attr,
            options=self.options,
        )
        if ret is None:
            return None
        props, module, parent = ret

        self.props = props
        self.module = module
        self.parent = parent
        self._load_object_has_been_called = True
        return True

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
        sourcename = self.get_sourcename()
        for line in _directive_header_lines(
            autodoc_typehints=self.config.autodoc_typehints,
            directive_name=directive_name,
            is_final=is_final,
            options=self.options,
            props=self.props,
        ):
            if line.strip():  # not a blank line
                result.append(indent + line, sourcename)
            else:
                result.append('', sourcename)

    def get_sourcename(self) -> str:
        obj_module = inspect.safe_getattr(self.props._obj, '__module__', None)
        obj_qualname = inspect.safe_getattr(self.props._obj, '__qualname__', None)
        if obj_module and obj_qualname:
            # Get the correct location of docstring from props._obj
            # to support inherited methods
            fullname = f'{self.props._obj.__module__}.{self.props._obj.__qualname__}'
        else:
            fullname = self.props.full_name

        if self.analyzer:
            return f'{self.analyzer.srcname}:docstring of {fullname}'
        else:
            return 'docstring of %s' % fullname

    def add_content(self, more_content: StringList | None, *, indent: str) -> None:
        """Add content from docstrings, attribute documentation and user."""
        # add content from docstrings
        processed_doc = StringList(
            list(
                self._process_docstrings(
                    self._get_docstrings(),
                    events=self._events,
                    props=self.props,
                    obj=self.props._obj,
                    options=self.options,
                )
            ),
            source=self.get_sourcename(),
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

    def _get_docstrings(self) -> list[list[str]] | None:
        """Add content from docstrings, attribute documentation and user."""
        if self.props._docstrings is not None:
            docstrings = [list(doc) for doc in self.props._docstrings]
        else:
            docstrings = None
        props = self.props

        if docstrings is not None and len(docstrings) == 0:
            # append at least a dummy docstring, so that the event
            # autodoc-process-docstring is fired and can add some
            # content if desired
            docstrings.append([])

        if props.obj_type in {'data', 'attribute'}:
            return docstrings

        attr_docs = None if self.analyzer is None else self.analyzer.find_attr_docs()
        if props.obj_type in {'class', 'exception'}:
            real_module = props._obj___module__ or props.module_name
            if props.module_name != real_module:
                try:
                    # override analyzer to obtain doc-comment around its definition.
                    ma = ModuleAnalyzer.for_module(props.module_name)
                    ma.analyze()
                    attr_docs = ma.attr_docs
                except PycodeError:
                    pass

        # add content from attribute documentation
        if attr_docs is not None and props.parts:
            key = ('.'.join(props.parent_names), props.name)
            if key in attr_docs:
                # make a copy of docstring for attributes to avoid cache
                # the change of autodoc-process-docstring event.
                return [list(attr_docs[key])]

        return docstrings

    @staticmethod
    def _process_docstrings(
        docstrings: list[list[str]] | None,
        *,
        events: EventManager,
        props: _ItemProperties,
        obj: Any,
        options: _AutoDocumenterOptions,
    ) -> Iterator[str]:
        """Let the user process the docstrings before adding them."""
        if docstrings is None:
            return
        for docstring_lines in docstrings:
            # let extensions preprocess docstrings
            events.emit(
                'autodoc-process-docstring',
                props.obj_type,
                props.full_name,
                obj,
                options,
                docstring_lines,
            )

            if docstring_lines and docstring_lines[-1]:
                # append a blank line to the end of the docstring
                docstring_lines.append('')

            yield from docstring_lines

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

    def generate(
        self,
        more_content: StringList | None = None,
        real_modname: str | None = None,
        check_module: bool = False,
        all_members: bool = False,
    ) -> None:
        """Generate reST for the object given by *self.name*, and possibly for
        its members.

        If *more_content* is given, include that content. If *real_modname* is
        given, use that module name to find attribute docs. If *check_module* is
        True, only generate if the object is defined in the module name it is
        imported from. If *all_members* is True, document all members.
        """
        if isinstance(self, ClassDocumenter):
            # Do not pass real_modname and use the name from the __module__
            # attribute of the class.
            # If a class gets imported into the module real_modname
            # the analyzer won't find the source of the class, if
            # it looks in real_modname.
            real_modname = None

        if self._load_object_by_name() is None:
            return

        self._generate(more_content, real_modname, check_module, all_members)

    def _generate(
        self,
        more_content: StringList | None = None,
        real_modname: str | None = None,
        check_module: bool = False,
        all_members: bool = False,
    ) -> None:
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
            # at least add the module.__file__ as a dependency
            if module___file__ := getattr(self.module, '__file__', ''):
                self.directive.record_dependencies.add(module___file__)
        else:
            self.directive.record_dependencies.add(self.analyzer.srcname)

        if self.real_modname != guess_modname:
            # Add module to dependency list if target object is defined in other module.
            try:
                analyzer = ModuleAnalyzer.for_module(guess_modname)
                self.directive.record_dependencies.add(analyzer.srcname)
            except PycodeError:
                pass

        has_docstring = any(self.props._docstrings or ())
        if ismock(self.props._obj) and not has_docstring:
            logger.warning(
                __('A mocked object is detected: %r'),
                self.name,
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
        sourcename = self.get_sourcename()

        # make sure that the result starts with an empty line.  This is
        # necessary for some situations where another directive preprocesses
        # reST and no starting newline is present
        self.directive.result.append('', sourcename)

        # generate the directive header and options, if applicable
        self.add_directive_header(indent=indent)
        self.directive.result.append('', sourcename)

        # add all content (from docstrings, attribute docs etc.)
        self.add_content(more_content, indent=indent)

        # document members, if possible
        has_members = isinstance(self, ModuleDocumenter) or (
            isinstance(self, ClassDocumenter) and not self.props.doc_as_attr
        )
        if has_members:
            want_all = bool(
                all_members
                or self.options.inherited_members
                or self.options.members is ALL
            )
            member_documenters = _gather_members(
                want_all=want_all,
                indent=indent,
                analyzer=self.analyzer,
                config=self.config,
                current_document=self._current_document,
                directive=self.directive,
                events=self._events,
                get_attr=self.get_attr,
                name=self.name,
                options=self.options,
                props=self.props,
                registry=self.env._registry,
            )

            # for implicit module members, check __module__ to avoid
            # documenting imported objects
            members_check_module = bool(
                isinstance(self, ModuleDocumenter)
                and want_all
                and (self.options.ignore_module_all or self.props.all is None)
            )
            _document_members(
                member_documenters=member_documenters,
                real_modname=self.real_modname,
                members_check_module=members_check_module,
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


def autodoc_attrgetter(
    obj: Any, name: str, *defargs: Any, registry: SphinxComponentRegistry
) -> Any:
    """Alternative getattr() for types"""
    for typ, func in registry.autodoc_attrgetters.items():
        if isinstance(obj, typ):
            return func(obj, name, *defargs)

    return safe_getattr(obj, name, *defargs)


def _document_members(
    *,
    member_documenters: list[tuple[Documenter, bool]],
    real_modname: str,
    members_check_module: bool,
) -> None:
    """Generate reST for member documentation.

    If *all_members* is True, document all members, else those given by
    *self.options.members*.
    """
    for documenter, is_attr in member_documenters:
        assert documenter.props.module_name
        # We can directly call ._generate() since the documenters
        # already called ``_load_object_by_name()`` before.
        #
        # Note that those two methods above do not emit events, so
        # whatever objects we deduced should not have changed.
        documenter._generate(
            all_members=True,
            real_modname=real_modname,
            check_module=members_check_module and not is_attr,
        )
